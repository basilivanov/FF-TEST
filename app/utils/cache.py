#!/usr/bin/env python3
"""
Простая система кеширования для UI endpoints.
"""

import time
import json
from typing import Dict, Any, Optional
from threading import Lock

class SimpleCache:
    """Простой in-memory кеш с TTL"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кеша"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if time.time() > entry['expires_at']:
                del self._cache[key]
                return None
            
            return entry['data']
    
    def set(self, key: str, data: Any, ttl_seconds: int = 300):
        """Сохранить в кеш с TTL"""
        with self._lock:
            self._cache[key] = {
                'data': data,
                'expires_at': time.time() + ttl_seconds,
                'created_at': time.time()
            }
    
    def delete(self, key: str):
        """Удалить из кеша"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Очистить весь кеш"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self):
        """Удалить просроченные записи"""
        current_time = time.time()
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if current_time > entry['expires_at']
            ]
            for key in expired_keys:
                del self._cache[key]
        return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """Статистика кеша"""
        with self._lock:
            current_time = time.time()
            active_entries = sum(
                1 for entry in self._cache.values() 
                if current_time <= entry['expires_at']
            )
            return {
                'total_entries': len(self._cache),
                'active_entries': active_entries,
                'expired_entries': len(self._cache) - active_entries
            }

# Глобальный экземпляр кеша
cache = SimpleCache()

# Предустановленные TTL для разных типов данных
CACHE_TTL = {
    'health_ready': 60,        # Health проверки кешируем на минуту
    'health_deps': 120,        # LLM агенты - на 2 минуты  
    'features': 30,            # Фичи обновляются часто
    'runs': 15,               # Запуски меняются быстро
    'tokens_summary': 300,     # Токены можно кешировать дольше
    'logs': 10,               # Логи почти реал-тайм
}

def get_cache_key(endpoint: str, params: Dict[str, Any] = None) -> str:
    """Генерирует ключ кеша на основе endpoint и параметров"""
    if params:
        param_str = json.dumps(params, sort_keys=True)
        return f"{endpoint}:{hash(param_str)}"
    return endpoint