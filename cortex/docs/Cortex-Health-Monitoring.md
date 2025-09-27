# Cortex Health Monitoring System

## Обзор

Система мониторинга здоровья кортекса автоматически анализирует полноту и качество документации в кортексе. Запускается каждый час и предоставляет метрики для оценки состояния базы знаний.

## Архитектура

### Компоненты

- **CortexAnalyzer** (`app/services/cortex_analyzer.py`) — основной анализатор
- **CortexScheduler** (`app/scheduler/cortex_jobs.py`) — планировщик задач
- **API Endpoints** (`app/api/cortex_health.py`) — REST API для получения данных
- **UI Dashboard** (`app/ui/src/pages/Docs.tsx`) — веб-интерфейс мониторинга

### База данных

Данные сохраняются в SQLite: `/opt/feature-factory/data/cortex_health.db`

**Таблицы:**
- `cortex_reports` — общие отчёты с timestamp и overall_score
- `role_metrics` — детальные метрики по ролям

## Метрики

### Общие метрики

- **Overall Score** (0-100%) — общий балл здоровья кортекса
- **Context Freshness** (0-100%) — свежесть контента (возраст файлов)
- **Role Coverage** (0-100%) — покрытие ролей документацией
- **Knowledge Completeness** (0-100%) — полнота базы знаний

### Метрики по ролям

Для каждой роли (architect, dev, qa, scribe, maintainer):

- **Doc Coverage** (0-100%) — покрытие документацией
- **Context Completeness** (0-100%) — полнота контекста
- **Content Freshness** (0-100%) — свежесть контента
- **Content Quality** (0-100%) — качество содержимого
- **Issues** — список выявленных проблем

### Алгоритм оценки качества

**Content Quality** рассчитывается на основе:
1. **Длина контента** (20%) — объём документации
2. **Структурированность** (30%) — заголовки, списки, примеры кода
3. **Специфичность** (25%) — соответствие типу файла
4. **Актуальность** (25%) — современные паттерны, отсутствие TODO/FIXME

## API Endpoints

### GET /cortex/health

Получение текущего состояния здоровья кортекса.

**Response:**
```json
{
  "overall_score": 75.8,
  "context_freshness": 95.2,
  "role_coverage": 4,
  "knowledge_completeness": 75.8,
  "last_updated": "2025-09-19T17:34:26Z",
  "roles": [
    {
      "role": "Dev",
      "context_quality": 95,
      "docs_count": 3,
      "last_updated": "2025-09-19T17:34:26Z",
      "issues": [],
      "icon": "Code"
    }
  ],
  "recommendations": [
    "Improve documentation for qa role",
    "Update outdated content for maintainer"
  ]
}
```

### POST /cortex/analyze

Запуск анализа кортекса в фоновом режиме.

**Response:**
```json
{
  "status": "Analysis started",
  "message": "Cortex analysis is running in background"
}
```

### GET /cortex/history?days=7

Получение истории анализов за указанное количество дней.

**Response:**
```json
{
  "period_days": 7,
  "overall_trend": [
    {
      "timestamp": "2025-09-19T17:34:26Z",
      "score": 75.8
    }
  ],
  "role_trends": {
    "dev": [
      {
        "timestamp": "2025-09-19T17:34:26Z",
        "score": 94.6
      }
    ]
  }
}
```

### GET /cortex/roles/{role}

Получение детальной информации о конкретной роли.

## Автоматизация

### Cron Job

Анализ запускается автоматически каждый час:
```bash
0 * * * * /opt/feature-factory/scripts/cortex-analyzer.sh
```

### Скрипт запуска

`/opt/feature-factory/scripts/cortex-analyzer.sh`:
- Проверяет, не запущен ли уже анализ
- Активирует virtual environment
- Запускает `python3 -m app.scheduler.cortex_jobs`
- Логирует результаты в `/opt/feature-factory/logs/cortex-analyzer.log`
- Еженедельно очищает старые отчёты (>30 дней)

## Мониторинг и алерты

### Критические пороги

- **Overall Score < 50%** — критическое состояние, логируется warning
- **Role Score < 50%** — проблемная роль, добавляется в critical_roles
- **Отсутствие файлов** — роль без cortex definition или prompts

### Логирование

События логируются с уровнями:
- `INFO` — нормальное выполнение анализа
- `WARNING` — критически низкие баллы
- `ERROR` — ошибки выполнения анализа

## Использование в UI

### Dashboard

Страница `/admin` → `Docs` отображает:
- Общие метрики здоровья кортекса
- Карточки ролей с баллами и проблемами
- Кнопка "Анализ кортекса" для ручного запуска
- История изменений и тренды

### Цветовая индикация

- **Зелёный** (85-100%) — отличное состояние
- **Жёлтый** (70-84%) — нормальное состояние
- **Красный** (<70%) — требует внимания

## Расширение системы

### Добавление новых метрик

1. Расширить `FileAnalysis` или `RoleAnalysis` классы
2. Обновить алгоритм в `_assess_content_quality()`
3. Добавить поля в API response format

### Добавление новых ролей

1. Добавить роль в `self.roles` списке `CortexAnalyzer`
2. Создать соответствующие файлы в `cortex/roles/` и `app/agents/prompts/`
3. Обновить иконки в UI (`getRoleIcon()`)

### Интеграция с алертами

Система готова к интеграции с внешними системами мониторинга через:
- REST API endpoints
- Структурированные логи
- Метрики в БД для построения графиков

## Troubleshooting

### Анализ не запускается

1. Проверить cron: `crontab -l`
2. Проверить логи: `tail -f /opt/feature-factory/logs/cortex-analyzer.log`
3. Запустить вручную: `python3 -m app.scheduler.cortex_jobs`

### API endpoints недоступны

1. Проверить что `cortex_health_router` включён в `app/main.py`
2. Перезапустить API сервер
3. Проверить `/openapi.json` на наличие `/cortex/*` endpoints

### Низкие баллы качества

1. Проверить структуру файлов (заголовки, списки, примеры)
2. Убрать TODO/FIXME из документации
3. Добавить современные ключевые слова (async, typescript, etc.)
4. Увеличить объём контента

## Версионирование

- **v1.0** (2025-09-19) — Базовая система анализа с 5 ролями
- Планируется: интеграция с Git для анализа изменений, ML-модели для оценки качества