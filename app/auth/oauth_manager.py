#!/usr/bin/env python3
"""
Автоматический OAuth менеджер для провайдеров LLM.
Обрабатывает refresh токены и автоматически обновляет access токены.
"""

import json
import time
import httpx
import structlog
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

logger = structlog.get_logger()

class OAuthManager:
    """Менеджер для автоматического обновления OAuth токенов."""
    
    def __init__(self):
        self.token_cache: Dict[str, Dict[str, Any]] = {}
        self.config_files = {
            'gemini': '/home/feature/.gemini/oauth_creds.json',
            'claude': '/home/feature/.claude.json'
        }
        
    def _load_token_file(self, provider: str) -> Optional[Dict[str, Any]]:
        """Загружает токены из файла конфигурации провайдера."""
        config_path = self.config_files.get(provider)
        if not config_path or not Path(config_path).exists():
            return None
            
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("failed_to_load_token_file", provider=provider, error=str(e))
            return None
    
    def _save_token_file(self, provider: str, data: Dict[str, Any]) -> bool:
        """Сохраняет обновленные токены в файл конфигурации."""
        config_path = self.config_files.get(provider)
        if not config_path:
            return False
            
        try:
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error("failed_to_save_token_file", provider=provider, error=str(e))
            return False
    
    def _is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Проверяет, истек ли access token."""
        expiry = token_data.get('expiry_date')
        if not expiry:
            return True
            
        # Добавляем 30 минут буфера для обновления (для надежности)
        buffer_seconds = 1800
        return (expiry / 1000) - time.time() < buffer_seconds
    
    def _refresh_google_token(self, refresh_token: str, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """Обновляет Google OAuth токен используя refresh token."""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(token_url, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                # Устанавливаем время истечения токена
                if 'expires_in' in token_data:
                    token_data['expiry_date'] = int((time.time() + token_data['expires_in']) * 1000)
                
                logger.info("oauth_token_refreshed", provider="google")
                return token_data
                
        except Exception as e:
            logger.error("failed_to_refresh_google_token", error=str(e))
            return None
    
    def _refresh_claude_token(self, refresh_token: str, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """Обновляет Claude OAuth токен используя refresh token."""
        # TODO: Добавить когда будет известен Claude OAuth endpoint
        logger.warning("claude_oauth_refresh_not_implemented")
        return None
    
    def get_valid_access_token(self, provider: str, oauth_config: Dict[str, Any]) -> Optional[str]:
        """
        Получает действительный access token для провайдера.
        Автоматически обновляет если токен истек.
        """
        # Сначала проверяем кэш
        cached = self.token_cache.get(provider)
        if cached and not self._is_token_expired(cached):
            return cached.get('access_token')
        
        # Загружаем токены из файла
        token_data = self._load_token_file(provider)
        if not token_data:
            logger.warning("no_token_file_found", provider=provider)
            return None
        
        # Проверяем, нужно ли обновлять токен
        if not self._is_token_expired(token_data):
            # Токен еще действителен, кэшируем и возвращаем
            self.token_cache[provider] = token_data
            return token_data.get('access_token')
        
        # Токен истек, обновляем его
        refresh_token = token_data.get('refresh_token')
        if not refresh_token:
            logger.error("no_refresh_token_found", provider=provider)
            return None
        
        client_id = oauth_config.get('client_id')
        client_secret = oauth_config.get('client_secret')
        
        if not client_id or not client_secret:
            logger.error("missing_oauth_credentials", provider=provider, config_keys=list(oauth_config.keys()))
            return None
        
        # Обновляем токен в зависимости от провайдера
        new_token_data = None
        if provider == 'gemini':
            new_token_data = self._refresh_google_token(refresh_token, client_id, client_secret)
        elif provider == 'claude':
            new_token_data = self._refresh_claude_token(refresh_token, client_id, client_secret)
        
        if not new_token_data:
            logger.error("failed_to_refresh_token", provider=provider)
            return None
        
        # Сохраняем refresh_token если он не пришел в ответе
        if 'refresh_token' not in new_token_data and refresh_token:
            new_token_data['refresh_token'] = refresh_token
        
        # Сохраняем обновленные токены
        updated_data = {**token_data, **new_token_data}
        if self._save_token_file(provider, updated_data):
            self.token_cache[provider] = updated_data
            logger.info("token_refreshed_and_saved", provider=provider)
            return updated_data.get('access_token')
        
        return None
    
    def inject_access_token(self, provider: str, oauth_config: Dict[str, Any], 
                          cmd: list, env: Dict[str, str]) -> bool:
        """
        Внедряет действительный access token в команду или переменные окружения.
        """
        access_token = self.get_valid_access_token(provider, oauth_config)
        if not access_token:
            return False
        
        # Определяем способ внедрения токена в зависимости от провайдера
        if provider == 'gemini':
            # Для Gemini устанавливаем переменную окружения
            env['GOOGLE_OAUTH_ACCESS_TOKEN'] = access_token
        elif provider == 'claude':
            # Для Claude добавляем флаг в команду
            if '--session-token' not in cmd:
                cmd.extend(['--session-token', access_token])
        
        logger.info("access_token_injected", provider=provider)
        return True
    
    def get_oauth_status(self) -> Dict[str, Dict[str, Any]]:
        """Получает статус OAuth для всех провайдеров."""
        status = {}
        
        for provider in self.config_files.keys():
            token_data = self._load_token_file(provider)
            if not token_data:
                status[provider] = {"status": "no_config", "message": "No token file found"}
                continue
            
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            
            if not access_token or not refresh_token:
                status[provider] = {"status": "incomplete", "message": "Missing tokens"}
                continue
            
            is_expired = self._is_token_expired(token_data)
            expiry_date = token_data.get('expiry_date')
            
            status[provider] = {
                "status": "expired" if is_expired else "valid",
                "has_refresh_token": bool(refresh_token),
                "expiry_date": datetime.fromtimestamp(expiry_date / 1000, tz=timezone.utc).isoformat() if expiry_date else None,
                "expires_in_seconds": (expiry_date / 1000 - time.time()) if expiry_date else None
            }
        
        return status


# Глобальный экземпляр OAuth менеджера
oauth_manager = OAuthManager()