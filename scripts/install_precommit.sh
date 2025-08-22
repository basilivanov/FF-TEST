#!/bin/bash
# Скрипт для установки pre-commit hook

set -euo pipefail

echo "Установка pre-commit hook..."

# Проверяем, что pre-commit установлен
if ! command -v pre-commit &> /dev/null
then
    echo "pre-commit не найден. Устанавливаем..."
    pip install pre-commit
fi

# Устанавливаем pre-commit hook
pre-commit install

echo "pre-commit hook установлен успешно!"
echo "Теперь при каждом коммите будет автоматически запускаться индексация измененных файлов."