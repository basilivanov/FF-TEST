#!/bin/bash
# Скрипт для запуска тестов миграций

echo "Запуск тестов миграций..."

# Активируем виртуальное окружение
source .venv/bin/activate

# Запускаем тесты
python -m pytest tests/test_migrations.py -v

echo "Тесты завершены."