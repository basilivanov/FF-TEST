#!/bin/bash
# Скрипт для запуска анализа кортекса.
# Может запускаться по cron каждый час.

set -euo pipefail

# Настройки
PROJECT_ROOT="/opt/feature-factory"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_FILE="/opt/feature-factory/logs/cortex-analyzer.log"
PID_FILE="/opt/feature-factory/data/cortex-analyzer.pid"

# Создаём директории если их нет
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$PID_FILE")"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Проверяем не запущен ли уже анализ
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log "Cortex analyzer is already running (PID: $OLD_PID)"
        exit 0
    else
        log "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Записываем PID текущего процесса
echo $$ > "$PID_FILE"

# Cleanup функция
cleanup() {
    rm -f "$PID_FILE"
}
trap cleanup EXIT

log "Starting cortex analysis..."

cd "$PROJECT_ROOT"

# Активируем virtual environment если он есть
if [[ -d "$VENV_PATH" ]]; then
    source "$VENV_PATH/bin/activate"
    log "Virtual environment activated"
fi

# Запускаем анализ
python3 -m app.scheduler.cortex_jobs 2>&1 | tee -a "$LOG_FILE"

# Проверяем результат
if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
    log "Cortex analysis completed successfully"
else
    log "Cortex analysis failed with exit code ${PIPESTATUS[0]}"
    exit 1
fi

# Раз в неделю очищаем старые отчёты
if [[ $(date +%u) -eq 1 ]] && [[ $(date +%H) -eq 2 ]]; then
    log "Running weekly cleanup..."
    python3 -m app.scheduler.cortex_jobs --cleanup --keep-days 30 2>&1 | tee -a "$LOG_FILE"
    log "Cleanup completed"
fi

log "Cortex analyzer finished"