#!/usr/bin/env python3
"""
Сервис кэширования статусов агентов с политикой SWR (stale-while-revalidate).
"""

from __future__ import annotations
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from app.db.session import SessionLocal
from app.api.llm_status import llm_status
import asyncio
from concurrent.futures import ThreadPoolExecutor


class AgentsStatusService:
    """
    Сервис кэширования статусов агентов с SWR политикой.
    TTL 5 минут, stale_on_error 10 минут.
    """
    
    def __init__(self):
        self.cache_ttl_minutes = 5
        self.stale_ttl_minutes = 10
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def get_cached_status(self, fresh: bool = False) -> Dict[str, Any]:
        """
        Получить статус агентов. Если fresh=True, принудительно обновить кэш.
        Возвращает данные в формате, совместимом с UI.
        """
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            
            if not fresh:
                # Пытаемся получить данные из кэша
                cached_data = self._get_from_cache(db, now)
                if cached_data:
                    return cached_data
            
            # Если кэша нет или fresh=True, получаем свежие данные
            fresh_data = self._fetch_fresh_data()
            self._update_cache(db, fresh_data, now)
            
            return self._format_response(fresh_data, now, stale=False)
            
        except Exception as e:
            # При ошибке пытаемся вернуть устаревший кэш
            stale_data = self._get_stale_from_cache(db, now)
            if stale_data:
                return stale_data
            
            # Если и устаревшего кэша нет, возвращаем ошибку
            return {
                "as_of": now.isoformat(),
                "stale": True,
                "error": str(e),
                "items": []
            }
        finally:
            db.close()
    
    def refresh_async(self) -> Dict[str, Any]:
        """
        Запускает асинхронное обновление кэша.
        Возвращает job_id для отслеживания.
        """
        job_id = f"refresh_{int(time.time())}"
        
        # Запускаем в фоне
        future = self._executor.submit(self._background_refresh)
        
        return {"job_id": job_id, "accepted": True}
    
    def _background_refresh(self):
        """Фоновое обновление кэша"""
        try:
            fresh_data = self._fetch_fresh_data()
            db = SessionLocal()
            try:
                self._update_cache(db, fresh_data, datetime.utcnow())
            finally:
                db.close()
        except Exception as e:
            # Логируем ошибку, но не прерываем работу
            print(f"Background refresh failed: {e}")
    
    def _get_from_cache(self, db, now: datetime) -> Optional[Dict[str, Any]]:
        """Получить действительные данные из кэша"""
        query = text("""
            SELECT model, provider, status, oauth_ok, tokens_used, 
                   latency_ms, checked_at, expires_at, meta_json
            FROM agents_status_cache 
            WHERE expires_at > :now
            ORDER BY model, provider
        """)
        
        result = db.execute(query, {"now": now}).fetchall()
        if not result:
            return None
            
        items = []
        for row in result:
            meta = json.loads(row.meta_json or '{}')
            items.append({
                "model": row.model,
                "provider": row.provider,
                "status": row.status,
                "oauth_ok": bool(row.oauth_ok),
                "tokens_used": row.tokens_used,
                "latency_ms": row.latency_ms,
                "checked_at": row.checked_at if isinstance(row.checked_at, str) else row.checked_at.isoformat(),
                "expires_at": row.expires_at if isinstance(row.expires_at, str) else row.expires_at.isoformat(),
                **meta
            })
        
        oldest_check = min((datetime.fromisoformat(item["checked_at"]) for item in items), default=now)
        return self._format_response_from_cache(items, oldest_check, stale=False)
    
    def _get_stale_from_cache(self, db, now: datetime) -> Optional[Dict[str, Any]]:
        """Получить устаревшие данные из кэша (для обработки ошибок)"""
        stale_cutoff = now - timedelta(minutes=self.stale_ttl_minutes)
        
        query = text("""
            SELECT model, provider, status, oauth_ok, tokens_used,
                   latency_ms, checked_at, expires_at, meta_json
            FROM agents_status_cache 
            WHERE checked_at > :stale_cutoff
            ORDER BY model, provider
        """)
        
        result = db.execute(query, {"stale_cutoff": stale_cutoff}).fetchall()
        if not result:
            return None
            
        items = []
        for row in result:
            meta = json.loads(row.meta_json or '{}')
            items.append({
                "model": row.model,
                "provider": row.provider,
                "status": row.status,
                "oauth_ok": bool(row.oauth_ok),
                "tokens_used": row.tokens_used,
                "latency_ms": row.latency_ms,
                "checked_at": row.checked_at if isinstance(row.checked_at, str) else row.checked_at.isoformat(),
                "expires_at": row.expires_at if isinstance(row.expires_at, str) else row.expires_at.isoformat(),
                **meta
            })
        
        oldest_check = min((datetime.fromisoformat(item["checked_at"]) for item in items), default=now)
        return self._format_response_from_cache(items, oldest_check, stale=True)
    
    def _fetch_fresh_data(self) -> Dict[str, Any]:
        """Получить свежие данные от API llm_status"""
        start_time = time.time()
        
        try:
            data = llm_status()
            latency = int((time.time() - start_time) * 1000)
            
            # Преобразуем в нужный формат
            items = []
            for provider_data in data.get("providers", []):
                provider = provider_data.get("provider", "unknown")
                auth = provider_data.get("auth", {})
                cli_probe = provider_data.get("cli_probe", {})
                
                items.append({
                    "model": provider,  # Используем provider как model
                    "provider": provider,
                    "status": "ok" if cli_probe.get("ok") else "error",
                    "oauth_ok": bool(auth.get("can_refresh_now")),
                    "tokens_used": None,  # Будет заполняться отдельно
                    "latency_ms": latency,
                    "binary_path": provider_data.get("binary_path"),
                    "probe_command": " ".join(provider_data.get("probe", [])),
                    "local_config_exists": auth.get("local_config_exists", False),
                    "has_refresh_token": auth.get("has_refresh_token", False),
                    "cli_error": cli_probe.get("stderr") or cli_probe.get("error")
                })
            
            return {
                "ts": data.get("ts", int(time.time())),
                "status": "ok",
                "items": items
            }
            
        except Exception as e:
            return {
                "ts": int(time.time()),
                "status": "error",
                "error": str(e),
                "items": []
            }
    
    def _update_cache(self, db, data: Dict[str, Any], now: datetime):
        """Обновить кэш в базе данных"""
        expires_at = now + timedelta(minutes=self.cache_ttl_minutes)
        
        # Очищаем старые записи
        db.execute(text("DELETE FROM agents_status_cache WHERE expires_at < :now"), {"now": now})
        
        # Вставляем новые данные
        for item in data.get("items", []):
            meta = {k: v for k, v in item.items() 
                   if k not in ["model", "provider", "status", "oauth_ok", "tokens_used", "latency_ms"]}
            
            db.execute(text("""
                INSERT OR REPLACE INTO agents_status_cache 
                (model, provider, status, oauth_ok, tokens_used, latency_ms, 
                 checked_at, expires_at, meta_json)
                VALUES (:model, :provider, :status, :oauth_ok, :tokens_used, :latency_ms,
                        :checked_at, :expires_at, :meta_json)
            """), {
                "model": item["model"],
                "provider": item["provider"], 
                "status": item["status"],
                "oauth_ok": item["oauth_ok"],
                "tokens_used": item["tokens_used"],
                "latency_ms": item["latency_ms"],
                "checked_at": now,
                "expires_at": expires_at,
                "meta_json": json.dumps(meta)
            })
        
        db.commit()
    
    def _format_response(self, data: Dict[str, Any], as_of: datetime, stale: bool) -> Dict[str, Any]:
        """Форматировать ответ для API"""
        return {
            "as_of": as_of.isoformat(),
            "stale": stale,
            "items": data.get("items", [])
        }
    
    def _format_response_from_cache(self, items: List[Dict[str, Any]], as_of: datetime, stale: bool) -> Dict[str, Any]:
        """Форматировать ответ из кэшированных данных"""
        return {
            "as_of": as_of.isoformat(),
            "stale": stale,
            "items": items
        }


# Глобальный экземпляр сервиса
agents_status_service = AgentsStatusService()