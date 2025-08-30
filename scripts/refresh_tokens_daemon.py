#!/usr/bin/env python3
"""
Автоматический планировщик обновления OAuth токенов.
Запускает refresh для всех провайдеров каждые 30 минут.
"""

import time
import sys
import os
from pathlib import Path

# Добавляем путь к модулям
sys.path.append('/opt/feature-factory')

from app.llm.providers.gemini import GeminiAdapter
from app.llm.providers.claude import ClaudeAdapter  
from app.llm.providers.qwen import QwenAdapter
from app.llm.providers.codex import CodexAdapter

def refresh_all_tokens():
    """Обновляет токены для всех провайдеров"""
    providers = [
        ("gemini", GeminiAdapter()),
        ("claude", ClaudeAdapter()),
        ("qwen", QwenAdapter()),
        ("codex", CodexAdapter())
    ]
    
    for provider_name, adapter in providers:
        try:
            # Получаем auth конфигурацию из provider_config
            auth_cfg = adapter.provider_config.get("auth", {})
            if not auth_cfg:
                print(f"[{provider_name}] No auth config found, skipping")
                continue
                
            # Пытаемся получить свежий токен
            new_token = adapter.get_fresh_access_token(auth_cfg)
            if new_token:
                # Обновляем локальный конфиг файл
                adapter.update_local_config_file(new_token, auth_cfg)
                print(f"[{provider_name}] Token refreshed successfully")
            else:
                print(f"[{provider_name}] Failed to refresh token")
                
        except Exception as e:
            print(f"[{provider_name}] Error during refresh: {e}")

def main():
    """Основной цикл демона"""
    print("Starting OAuth token refresh daemon...")
    
    while True:
        try:
            print(f"Refreshing tokens at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            refresh_all_tokens()
            print("Waiting 30 minutes until next refresh...")
            time.sleep(1800)  # 30 минут
        except KeyboardInterrupt:
            print("Daemon stopped by user")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            print("Waiting 5 minutes before retry...")
            time.sleep(300)  # 5 минут при ошибке

if __name__ == "__main__":
    main()