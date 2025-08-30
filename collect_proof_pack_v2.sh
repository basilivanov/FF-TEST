#!/bin/bash

# Скрипт для сбора "пруфов" о состоянии сервиса feature-factory-test

# 1. Генерируем уникальный ID для этого запуска
RUN_ID="proof_pack_$(date +%Y%m%d_%H%M%S)"
OUTPUT_DIR="/opt/feature-factory/tmp/$RUN_ID"
OUTPUT_FILE="$OUTPUT_DIR/proofs.txt"

# 2. Создаем директорию для артефактов
mkdir -p "$OUTPUT_DIR"
echo "Директория для артефактов: $OUTPUT_DIR"

# 3. Собираем информацию о сервисе
echo "### systemctl show feature-factory-test.service ###" > "$OUTPUT_FILE"
systemctl show feature-factory-test.service | grep -E 'User=|Group=|Restart=' >> "$OUTPUT_FILE"
echo -e "\n\n" >> "$OUTPUT_FILE"

# 4. Проверяем health check
echo "### Health Check: /health/live ###" >> "$OUTPUT_FILE"
curl -sS http://127.0.0.1:8081/health/live >> "$OUTPUT_FILE"
echo -e "\n\n" >> "$OUTPUT_FILE"

# 5. Проверяем API endpoint
echo "### API Check: /api/v1/context/?task_description=ping ###" >> "$OUTPUT_FILE"
curl -sS http://127.0.0.1:8081/api/v1/context/?task_description=ping >> "$OUTPUT_FILE"
echo -e "\n\n" >> "$OUTPUT_FILE"

# 6. Собираем логи сервиса
echo "### Logs: journalctl -u feature-factory-test.service -n 80 ###" >> "$OUTPUT_FILE"
journalctl -u feature-factory-test.service -n 80 --no-pager >> "$OUTPUT_FILE"

echo "Сбор пруфов завершен. Результаты сохранены в: $OUTPUT_FILE"
