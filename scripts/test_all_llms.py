#!/usr/bin/env python3
"""
Скрипт для тестирования всех комбинаций "роль + модель".
"""

import sys
import os
import yaml
from typing import List, Dict, Any

# Добавляем путь к приложению в sys.path, чтобы можно было импортировать модули
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.llm.router import completion, RETRYABLE_ERROR, _filter_providers_by_mode

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

def test_role_model_combination(role: str, providers: List[str], mode: str = None) -> bool:
    """
    Тестирует комбинацию роль+модель.
    
    Args:
        role: Роль агента.
        providers: Список провайдеров для роли.
        mode: Режим работы ('reasoning' или 'fast').
        
    Returns:
        True, если тест прошел успешно, False в противном случае.
    """
    print(f"\n--- Тестирование роли '{role}' с провайдерами {providers} в режиме '{mode or 'default'}' ---")
    
    # Тестовое сообщение
    test_messages = [
        {
            "role": "user",
            "content": "Ответь очень кратко: Какой цвет неба?"
        }
    ]
    
    try:
        # Выполняем запрос
        result = completion(
            role=role,
            messages=test_messages,
            max_tokens=50,
            temperature=0.1,
            mode=mode
        )
        
        # Проверяем результат
        if result and isinstance(result, dict):
            # Проверяем, есть ли текст в ответе
            text = ""
            if "choices" in result and result["choices"]:
                text = result["choices"][0]["message"]["content"]
            elif "text" in result:
                text = result["text"]
                
            if text:
                print(f"  ✅ УСПЕХ: Получен ответ от {result.get('provider', 'unknown')} ({result.get('model', 'unknown')}): {text[:50]}...")
                return True
            else:
                print(f"  ❌ ОШИБКА: Ответ пустой")
                return False
        else:
            print(f"  ❌ ОШИБКА: Некорректный формат ответа: {result}")
            return False
            
    except RETRYABLE_ERROR as e:
        print(f"  ⚠️  ПРЕДУПРЕЖДЕНИЕ: Ошибка, которую можно повторить: {e}")
        return False
    except Exception as e:
        print(f"  ❌ ОШИБКА: {e}")
        return False

def test_qwen_restriction(role: str, providers: List[str], role_cfg: Dict[str, Any]) -> bool:
    """
    Проверяет, что Qwen не используется в режиме 'reasoning'.
    
    Args:
        role: Роль агента.
        providers: Список провайдеров для роли.
        role_cfg: Конфигурация роли.
        
    Returns:
        True, если ограничение соблюдено, False в противном случае.
    """
    print(f"\n--- Проверка ограничения Qwen для роли '{role}' в режиме 'reasoning' ---")
    
    # Фильтруем провайдеры для режима 'reasoning'
    filtered_providers = _filter_providers_by_mode(providers, role_cfg, 'reasoning')
    
    # Проверяем, есть ли Qwen в отфильтрованном списке
    qwen_providers = [p for p in filtered_providers if p.startswith('qwen')]
    
    if qwen_providers:
        print(f"  ❌ НАРУШЕНИЕ: Qwen провайдеры {qwen_providers} присутствуют в режиме 'reasoning' для роли '{role}'")
        return False
    else:
        print(f"  ✅ СОБЛЮДЕНО: Qwen провайдеры отсутствуют в режиме 'reasoning' для роли '{role}'")
        return True

def main():
    """Основная функция скрипта."""
    print("Начало тестирования всех комбинаций 'роль + модель'...")
    
    # Загружаем конфигурацию
    routing_config = load_routing_config()
    if not routing_config:
        print("Не удалось загрузить конфигурацию. Завершение работы.")
        return 1
    
    roles_config = routing_config.get('roles', {})
    if not roles_config:
        print("В конфигурации не найдены роли. Завершение работы.")
        return 1
    
    # Счетчики для статистики
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # Тестируем каждую роль
    for role, role_cfg in roles_config.items():
        providers = role_cfg.get('providers', [])
        if not providers:
            print(f"\n--- Роль '{role}' не имеет провайдеров. Пропуск. ---")
            continue
            
        # Тест в режиме по умолчанию (все провайдеры)
        total_tests += 1
        if test_role_model_combination(role, providers):
            passed_tests += 1
        else:
            failed_tests += 1
            
        # Тест в режиме 'reasoning', если роль поддерживает сложные рассуждения
        reasoning_effort = role_cfg.get('reasoning_effort', 'minimal')
        extended_thinking = role_cfg.get('extended_thinking', False)
        adaptive_thinking = role_cfg.get('adaptive_thinking', False)
        
        if reasoning_effort == 'high' or extended_thinking or adaptive_thinking:
            total_tests += 1
            if test_role_model_combination(role, providers, 'reasoning'):
                passed_tests += 1
            else:
                failed_tests += 1
                
        # Тест в режиме 'fast', если роль поддерживает минимальные рассуждения
        if reasoning_effort == 'minimal':
            total_tests += 1
            if test_role_model_combination(role, providers, 'fast'):
                passed_tests += 1
            else:
                failed_tests += 1
                
        # Проверка ограничения для Qwen
        # Если роль имеет Qwen в провайдерах и поддерживает режим 'reasoning'
        if any(p.startswith('qwen') for p in providers) and (reasoning_effort == 'high' or extended_thinking or adaptive_thinking):
            total_tests += 1
            if test_qwen_restriction(role, providers, role_cfg):
                passed_tests += 1
            else:
                failed_tests += 1
    
    # Выводим итоговую статистику
    print("\n" + "="*60)
    print("ИТОГОВАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ")
    print("="*60)
    print(f"Всего тестов: {total_tests}")
    print(f"Успешно пройдено: {passed_tests}")
    print(f"Провалено: {failed_tests}")
    
    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        print(f"Процент успеха: {success_rate:.2f}%")
    
    if failed_tests > 0:
        print("\n⚠️  Некоторые тесты завершились неудачей. Проверьте логи выше.")
        return 1
    else:
        print("\n✅ Все тесты успешно пройдены!")
        return 0

if __name__ == "__main__":
    sys.exit(main())