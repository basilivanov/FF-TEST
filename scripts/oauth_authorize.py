#!/usr/bin/env python3
"""
Скрипт для первичной OAuth авторизации провайдеров.
Запускает CLI провайдера, который покажет ссылку для авторизации в браузере.
"""

import sys
import subprocess
from pathlib import Path

def authorize_gemini():
    """Запускает Gemini CLI для первичной авторизации."""
    print("🔐 Запуск Gemini OAuth авторизации...")
    print("Gemini CLI покажет ссылку - перейдите по ней в браузере и авторизуйтесь")
    print()
    
    try:
        # Запускаем Gemini CLI для авторизации
        result = subprocess.run([
            "/opt/feature-factory/bin/ff-cli-wrapper.sh", 
            "/usr/local/bin/gemini", 
            "-p", "Hello"
        ], 
        env={"HOME": "/home/feature"}, 
        timeout=300,
        capture_output=False  # Показываем вывод пользователю
        )
        
        if result.returncode == 0:
            print("✅ Gemini авторизация завершена!")
        else:
            print("❌ Ошибка авторизации Gemini")
            
    except subprocess.TimeoutExpired:
        print("⏰ Таймаут авторизации - попробуйте еще раз")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def authorize_claude():
    """Запускает Claude CLI для первичной авторизации.""" 
    print("🔐 Запуск Claude OAuth авторизации...")
    print("Claude CLI покажет ссылку - перейдите по ней в браузере и авторизуйтесь")
    print()
    
    try:
        # Запускаем Claude CLI для авторизации  
        result = subprocess.run([
            "/opt/feature-factory/bin/ff-cli-wrapper.sh",
            "/usr/local/bin/claude", 
            "messages", "create",
            "--dangerously-skip-permissions"
        ],
        env={"HOME": "/home/feature"},
        timeout=300, 
        capture_output=False,
        input='[{"role": "user", "content": "Hello"}]',
        text=True
        )
        
        if result.returncode == 0:
            print("✅ Claude авторизация завершена!")
        else:
            print("❌ Ошибка авторизации Claude")
            
    except subprocess.TimeoutExpired:
        print("⏰ Таймаут авторизации - попробуйте еще раз")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 oauth_authorize.py gemini   # Авторизация Gemini")
        print("  python3 oauth_authorize.py claude   # Авторизация Claude")
        print("  python3 oauth_authorize.py all      # Авторизация всех провайдеров")
        return
    
    provider = sys.argv[1].lower()
    
    if provider == "gemini":
        authorize_gemini()
    elif provider == "claude": 
        authorize_claude()
    elif provider == "all":
        print("🚀 Авторизация всех провайдеров...")
        print()
        authorize_gemini()
        print()
        authorize_claude()
    else:
        print(f"❌ Неизвестный провайдер: {provider}")
        print("Доступные: gemini, claude, all")

if __name__ == "__main__":
    main()