# CLI Commands Reference

## LLM Wrapper Commands (OAuth authorized)

### claude
```bash
# Интерактивный чат
claude --dangerously-skip-permissions -p "Your prompt here"

# Pipe input
echo "prompt" | claude --dangerously-skip-permissions -p "Process this"
```

### gemini 
```bash
# Простой prompt
gemini -p "Your prompt here"

# С флагами
gemini -y -p "Your prompt with confirmation"
```

### qwen
```bash
# Стандартный вызов
qwen -p "Your prompt"

# С auto-yes
qwen -y -p "Your prompt"
```

### codex
```bash  
# Интерактивный режим
codex --dangerously-bypass-approvals-and-sandbox

# Pipe режим с JSON выводом
echo "prompt" | codex --json
```

## FeatureFactory Admin Commands (nosudo)

### Bootstrap команды
```bash
# Полная инициализация системы
ff-admin-bootstrap-nosudo

# Быстрая инициализация 
ff-admin-bootstrap-quick-nosudo

# Post-start hook
ff-orch-poststart-hook-nosudo
```

### Runner управление
```bash
# Запуск runner'а
ff-runner-start-nosudo

# Остановка runner'а  
ff-runner-stop-nosudo

# Статус runner'а
ff-runner-status-nosudo

# Рестарт оркестратора
ff-orch-restart-safe
```

### UI команды
```bash
# Сборка UI
ff-ui-build-nosudo

# Деплой UI с smoke тестами
ff-ui-deploy-safe-nosudo --smoke

# Только деплой без smoke
ff-ui-deploy-safe-nosudo
```

### Task выполнение
```bash  
# Запуск задачи с correlation ID
ff-task-run-nosudo --corr C-$(date +%s) -- claude -p "Your task"

# Универсальный wrapper
env HOME=/home/feature bash -lc "exec \"$REAL_BINARY_PATH\" \"$@\"" -- "$@"
```

## Database Commands

### Alembic миграции
```bash
# Создание миграции (всегда из корня проекта)
cd /opt/feature-factory
alembic revision --autogenerate -m "descriptive message"

# Применение миграций
alembic upgrade head

# Откат последней миграции
alembic downgrade -1
```

### Database операции
```bash
# Smoke тест БД
scripts/ops/db_rw_smoke.sh

# WAL режим проверка
scripts/ci/wal_smoke.sh

# Backup smoke тест
scripts/ci/db_backup_smoke.sh
```

## CI/CD Scripts

### Smoke тесты
```bash
# Health ready цепочка
scripts/ci/health_ready_smoke.sh

# Метрики
scripts/ci/metrics_smoke.sh

# Runner метрики  
scripts/ci/runner_metrics_smoke.sh

# SSE runner
scripts/ci/ui_sse_runner_smoke.sh

# UI live тест
scripts/ci/ui_runner_live_smoke.sh

# Well-known endpoint
scripts/ci/well_known_smoke.sh

# E2E тест
scripts/ci/d5_e2e.sh
```

### Environment setup
```bash
# Настройка E2E
scripts/setup_e2e.sh

# Начальная индексация
scripts/run_initial_indexing.sh

# Авторизация провайдеров
scripts/authorize_providers.py
```

## Git Operations

### Standard flow
```bash
# Проверка статуса
git status

# Создание ветки
git checkout -b feature/12345_new_feature

# Коммит с proper message
git commit -m "feat(scope): description

Correlation ID: CORR_12345"

# Push с upstream
git push -u origin feature/12345_new_feature
```

### SSH Key setup  
```bash
# Генерация ключа
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_ff

# SSH config
cat >> ~/.ssh/config << EOF
Host github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_ff  
  IdentitiesOnly yes
EOF
```

## System Monitoring

### Service management
```bash
# Статус сервисов
systemctl status feature-factory-test.service
systemctl status feature-factory-runner.service

# Логи сервисов
journalctl -u feature-factory-test.service -f
journalctl -u feature-factory-runner.service -f
```

### Health checks
```bash
# API health
curl http://127.0.0.1:8081/health/live

# Metrics check
curl http://127.0.0.1:8081/api/v1/metrics

# Context endpoint
curl http://127.0.0.1:8081/.well-known/ff-context.json
```