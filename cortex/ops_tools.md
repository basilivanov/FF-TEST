# Ops Tools (sudo wrappers)

This document lists the available `sudo` wrappers and their intended use.

## Cortex Health Monitoring (v2.8.0+)

### Overview
Автоматическая система мониторинга здоровья кортекса. Анализирует полноту документации, качество контента и предоставляет метрики для оценки состояния базы знаний.

### Commands
```bash
# Запуск анализа вручную
python3 -m app.scheduler.cortex_jobs

# Проверка cron job (запускается каждый час)
crontab -l

# Просмотр логов анализа
tail -f /opt/feature-factory/logs/cortex-analyzer.log

# Запуск интеграционных тестов
python3 /opt/feature-factory/test_cortex_analyzer.py

# Проверка базы данных
sqlite3 /opt/feature-factory/data/cortex_health.db "SELECT timestamp, overall_score FROM cortex_reports ORDER BY timestamp DESC LIMIT 5;"
```

### API Endpoints
- `GET /cortex/health` — текущее состояние кортекса
- `POST /cortex/analyze` — запуск анализа в фоне
- `GET /cortex/history?days=7` — история за период
- `GET /cortex/roles/{role}` — детали по роли

### Мониторинг
- **Нормально**: Overall Score > 70%, все роли документированы
- **Критично**: Overall Score < 50%, missing cortex definition

## Sudo Wrappers

- `ff-free-8081`: Frees up port 8081.
- `ff-logs-read`: Reads system logs.
- `ff-netdiag-8081`: Runs network diagnostics on port 8081.
- `ff-nginx-reload-safe`: Safely reloads the NGINX configuration.
- `ff-ops-acceptance`: Runs operational acceptance tests.
- `ff-orch-restart-safe`: Safely restarts the application orchestrator.
- `ff-orch-start-safe`: Safely starts the application orchestrator.
- `ff-orch-status-safe`: Safely checks the status of the application orchestrator.
- `ff-orch-stop-safe`: Safely stops the application orchestrator.
- `ff-ui-deploy-safe`: Safely deploys the user interface.
