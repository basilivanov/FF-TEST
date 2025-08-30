#!/usr/bin/env python3
"""
Скрипт для тестирования ограничения на использование Qwen в режиме 'reasoning'.
"""

import sys
import os
import yaml
from typing import List, Dict, Any

# Добавляем путь к приложению в sys.path, чтобы можно было импортировать модули
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.llm.router import _filter_providers_by_mode

# Путь к конфигурационному файлу роутинга
ROUTING_CONFIG_PATH = "/opt/feature-factory/configs/llm_routing.yaml"

def load_routing_config() -> Dict[str, Any]:
    """Загружает конфигурацию роутинга из файла."""
    try:
        with open(ROUTING_CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации: {e}")
        return {}

def test_qwen_restriction():
    """Тестирует ограничение на использование Qwen в режиме 'reasoning'."""
    print("Тестирование ограничения на использование Qwen в режиме 'reasoning'...")
    
    # Загружаем конфигурацию
    routing_config = load_routing_config()
    if not routing_config:
        print("Не удалось загрузить конфигурацию. Завершение работы.")
        return False
    
    roles_config = routing_config.get('roles', {})
    
    # Берем конфигурацию роли Dev, которая имеет Qwen в провайдерах
    role_cfg = roles_config.get('Dev', {})
    providers = role_cfg.get('providers', [])
    
    print(f"  Конфигурация роли Dev: {role_cfg}")
    print(f"  Провайдеры для роли Dev: {providers}")
    
    # Фильтруем провайдеры для режима 'reasoning'
    filtered_providers = _filter_providers_by_mode(providers, role_cfg, 'reasoning')
    
    print(f"  Отфильтрованные провайдеры в режиме 'reasoning': {filtered_providers}")
    
    # Проверяем, что Qwen отсутствует в отфильтрованном списке
    qwen_providers = [p for p in filtered_providers if p.startswith('qwen')]
    
    if qwen_providers:
        print(f"  ❌ НАРУШЕНИЕ: Qwen провайдеры {qwen_providers} присутствуют в режиме 'reasoning'")
        return False
    else:
        print(f"  ✅ СОБЛЮДЕНО: Qwen провайдеры отсутствуют в режиме 'reasoning'")
        return True

def test_qwen_allowed_in_fast():
    """Тестирует, что Qwen разрешен в режиме 'fast'."""
    print("\nТестирование разрешения Qwen в режиме 'fast'...")
    
    # Загружаем конфигурацию
    routing_config = load_routing_config()
    if not routing_config:
        print("Не удалось загрузить конфигурацию. Завершение работы.")
        return False
    
    roles_config = routing_config.get('roles', {})
    
    # Берем конфигурацию роли Dev, которая имеет Qwen в провайдерах
    role_cfg = roles_config.get('Dev', {})
    providers = role_cfg.get('providers', [])
    
    print(f"  Конфигурация роли Dev: {role_cfg}")
    print(f"  Провайдеры для роли Dev: {providers}")
    
    # Фильтруем провайдеры для режима 'fast'
    filtered_providers = _filter_providers_by_mode(providers, role_cfg, 'fast')
    
    print(f"  Отфильтрованные провайдеры в режиме 'fast': {filtered_providers}")
    
    # Проверяем, что Qwen присутствует в отфильтрованном списке
    qwen_providers = [p for p in filtered_providers if p.startswith('qwen')]
    
    if qwen_providers:
        print(f"  ✅ СОБЛЮДЕНО: Qwen провайдеры {qwen_providers} присутствуют в режиме 'fast'")
        return True
    else:
        print(f"  ❌ НАРУШЕНИЕ: Qwen провайдеры отсутствуют в режиме 'fast'")
        return False

def test_high_reasoning_role_with_qwen():
    """Тестирует, что для роли с высоким уровнем рассуждений Qwen не используется в режиме 'reasoning'."""
    print("\nТестирование ограничения Qwen для роли с высоким уровнем рассуждений в режиме 'reasoning'...")
    
    # Создаем тестовую конфигурацию роли с высоким уровнем рассуждений и Qwen в провайдерах
    role_cfg = {
        'providers': ['qwen_code', 'gemini_25_pro', 'openai_gpt5_via_codex'],
        'reasoning_effort': 'high',
        'extended_thinking': True,
        'adaptive_thinking': True,
        'json_mode': 'json_schema',
        'json_schema_ref': 'configs/schemas/maintainer.intent.schema.json',
        'timeout_sec': 55
    }
    
    providers = role_cfg.get('providers', [])
    
    print(f"  Тестовая конфигурация роли: {role_cfg}")
    print(f"  Провайдеры: {providers}")
    
    # Фильтруем провайдеры для режима 'reasoning'
    filtered_providers = _filter_providers_by_mode(providers, role_cfg, 'reasoning')
    
    print(f"  Отфильтрованные провайдеры в режиме 'reasoning': {filtered_providers}")
    
    # Проверяем, что Qwen отсутствует в отфильтрованном списке
    qwen_providers = [p for p in filtered_providers if p.startswith('qwen')]
    
    # Также проверяем, что другие провайдеры присутствуют
    other_providers = [p for p in filtered_providers if not p.startswith('qwen')]
    
    if qwen_providers:
        print(f"  ❌ НАРУШЕНИЕ: Qwen провайдеры {qwen_providers} присутствуют в режиме 'reasoning'")
        return False
    elif not other_providers:
        print(f"  ❌ НАРУШЕНИЕ: Нет других провайдеров в режиме 'reasoning'")
        return False
    else:
        print(f"  ✅ СОБЛЮДЕНО: Qwen провайдеры отсутствуют в режиме 'reasoning', другие провайдеры {other_providers} присутствуют")
        return True

def main():
    """Основная функция скрипта."""
    print("Начало тестирования ограничений для Qwen...")
    
    # Запускаем тесты
    test1_passed = test_qwen_restriction()
    test2_passed = test_qwen_allowed_in_fast()
    test3_passed = test_high_reasoning_role_with_qwen()
    
    # Выводим итоговый результат
    print("\n" + "="*60)
    print("ИТОГОВЫЙ РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ ОГРАНИЧЕНИЙ QWEN")
    print("="*60)
    
    if test1_passed and test2_passed and test3_passed:
        print("✅ Все тесты ограничений для Qwen пройдены успешно!")
        return 0
    else:
        print("❌ Некоторые тесты ограничений для Qwen завершились неудачей.")
        return 1

if __name__ == "__main__":
    sys.exit(main())