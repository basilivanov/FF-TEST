#!/usr/bin/env python3
"""
Автоматический планировщик обновления OAuth токенов.
Запускает refresh для всех провайдеров каждые 30 минут.
"""

import time
import sys
import os
import yaml
import json
import subprocess
from pathlib import Path

# Добавляем путь к модулям
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

def load_config():
    """Загружает llm_cli_config.yaml"""
    config_path = PROJECT_ROOT / "configs/llm_cli_config.yaml"
    if not config_path.exists():
        raise RuntimeError(f"Config not found: {config_path}")
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))

def refresh_oauth_token(provider_name, auth_config):
    """Обновляет OAuth токен для провайдера через authorize_providers.py"""
    try:
        refresh_key = auth_config.get("refresh_secret_key")
        if not refresh_key:
            print(f"[{provider_name}] No refresh_secret_key configured")
            return False
            
        # Вызываем authorize_providers.py для обновления токена
        cmd = [
            "python3", 
            str(PROJECT_ROOT / "scripts/authorize_providers.py"),
            "oauth",
            "--provider", provider_name
        ]
        
        # Запускаем с виртуальным окружением
        venv_python = PROJECT_ROOT / ".venv/bin/python3"
        if venv_python.exists():
            cmd[0] = str(venv_python)
            
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"[{provider_name}] OAuth refresh completed")
            return True
        else:
            print(f"[{provider_name}] OAuth refresh failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[{provider_name}] Error during OAuth refresh: {e}")
        return False

def check_local_token_file(provider_name, auth_config):
    """Проверяет срок действия локального токена"""
    try:
        local_file = auth_config.get("local_config_file")
        if not local_file or not Path(local_file).exists():
            return False
            
        with open(local_file, 'r') as f:
            token_data = json.load(f)
            
        # Простая проверка времени истечения (если есть)
        expiry = token_data.get("expiry_date")
        if expiry and expiry < time.time() * 1000:
            print(f"[{provider_name}] Token expired, needs refresh")
            return False
            
        print(f"[{provider_name}] Token still valid")
        return True
        
    except Exception as e:
        print(f"[{provider_name}] Error checking token: {e}")
        return False

def refresh_all_tokens():
    """Обновляет токены для всех провайдеров"""
    try:
        config = load_config()
        providers = config.get("providers", {})
        
        for provider_name, provider_config in providers.items():
            auth_config = provider_config.get("auth", {})
            if not auth_config:
                print(f"[{provider_name}] No auth config found, skipping")
                continue
                
            # Проверяем актуальность токена
            if check_local_token_file(provider_name, auth_config):
                continue
                
            # Пытаемся обновить токен
            refresh_oauth_token(provider_name, auth_config)
                
    except Exception as e:
        print(f"Error loading config or refreshing tokens: {e}")

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