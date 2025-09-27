#!/usr/bin/env bash
set -euo pipefail

# Импортируем библиотеку для логирования
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$APP_DIR/logs/index.log"

# Функция для логирования
log() {
    local level=$1
    local message=$2
    local timestamp=$(date -Iseconds)
    echo "{\"ts\":\"$timestamp\",\"level\":\"$level\",\"component\":\"index\",\"event\":\"$message\"}" >> "$LOG_FILE"
}

# Создаем директорию для логов, если она не существует
mkdir -p "$APP_DIR/logs"

# Начало индексации
log "INFO" "index_started"

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$APP_DIR/app/index"
mkdir -p "$OUT_DIR"

# Запускаем скрипт обновления реестра кода с новой базой данных
echo "Запускаем обновление реестра кода и индексов..."
log "INFO" "update_code_registry_started"
# removed DATABASE_URL override to use defaults
"$APP_DIR/.venv/bin/python3" "$APP_DIR/scripts/update_code_registry.py"
log "INFO" "update_code_registry_completed"

# Индексируем код с помощью ctags
echo "Запускаем индексацию кода с помощью ctags..."
log "INFO" "ctags_index_started"
# Удаляем существующий файл символов
rm -f "$OUT_DIR/symbols.json"
# Используем более простую команду для ctags
ctags --extras=+p --fields=+S --output-format=json -f "$OUT_DIR/symbols.json" --languages=python $(find "$APP_DIR/app" -name "*.py" -type f)
log "INFO" "ctags_index_completed"

# Генерируем граф вызовов с помощью pyan3
echo "Генерируем граф вызовов с помощью pyan3..."
log "INFO" "pyan3_index_started"
# Удаляем существующий файл графа вызовов
rm -f "$OUT_DIR/call_graph.dot"
# Используем более простую команду для pyan3
"$APP_DIR/.venv/bin/pyan3" $(find "$APP_DIR/app" -name "*.py" -type f) --uses --no-defines --colored --grouped --annotated --dot > "$OUT_DIR/call_graph.dot"
log "INFO" "pyan3_index_completed"

# Генерируем статус индексации
echo "{\"status\":\"completed\",\"indexed_at\":\"$(date -Iseconds)\",\"msg\":\"Индексация завершена успешно\"}" > "$OUT_DIR/index_status.json"
echo "Index status written to $OUT_DIR/index_status.json"

# Логируем завершение индексации
log "INFO" "index_updated"
