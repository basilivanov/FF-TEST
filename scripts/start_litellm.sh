#!/bin/bash
# Скрипт для запуска LiteLLM proxy

set -euo pipefail

# Используем виртуальное окружение проекта
export PATH="/opt/feature-factory/.venv/bin:$PATH"

# Проверяем, что LiteLLM установлен
if ! command -v litellm &> /dev/null
then
    echo "LiteLLM не найден в виртуальном окружении."
    exit 1
fi

# Запускаем LiteLLM proxy с конфигурацией
echo "Запускаем LiteLLM proxy..."
litellm --config /opt/feature-factory/configs/litellm.yaml --port 4000