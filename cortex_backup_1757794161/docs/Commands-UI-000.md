# Commands-UI-000: Команды админки

## Общее описание

Документ описывает команды, доступные в веб-интерфейсе админки Feature Factory.

## Навигация

### Dashboard
- Просмотр карточек System Health, Backlog, Runs, LLM Budgets, Errors, Docs
- ENV banner показывает текущее окружение (TEST)

### Features / Backlog
- Просмотр списка фич с фильтрацией по статусу
- Действия с фичами:
  - Plan: запланировать выполнение фичи
  - Run: запустить выполнение фичи
  - Pause: приостановить выполнение фичи (временно недоступно)
  - Retry: повторить выполнение фичи
  - Promote: продвинуть фичу (временно недоступно)
- Просмотр деталей фичи:
  - Список задач
  - Текущий run_id
  - История выполнения

### Tasks
- Просмотр списка последних задач
- Фильтрация по роли и статусу
- Просмотр деталей задачи

### Runs (Graph)
- Просмотр списка последних запусков графов
- Просмотр статуса конкретного запуска по run_id
- Кнопка Resume для возобновления прерванного запуска

### Logs (tail)
- Просмотр потока логов в реальном времени
- Фильтрация логов по компоненту, уровню, событию, роли агента
- Автопрокрутка к последним записям
- Пауза потока логов
- Копирование отдельных записей логов

### Tokens
- Просмотр сводки расхода токенов по дням, ролям и моделям

### Docs
- Просмотр списка документов из реестра
- Просмотр версии, хэша и даты обновления каждого документа
- Кнопка Docs Rebuild для пересборки документации

### Settings
- Просмотр настроек системы (только чтение):
  - APP_TZ (часовой пояс приложения)
  - Расписания
  - Идентификаторы систем

### Chat (Maintainer)
- Ввод команд на естественном языке
- Предпросмотр сгенерированного intent и DAG
- Кнопки:
  - Создать фичу: создает новую фичу на основе введенного описания
  - Сразу выполнить: немедленно выполняет команду (если возможно)

## API Endpoints

### Orchestrator

POST /api/v1/orchestrator/features
- Создание новой фичи
- Параметры: title, intent_json
- Ответ: id, status

POST /api/v1/orchestrator/features/{id}/plan
- Планирование выполнения фичи
- Ответ: список задач, package_contract

POST /api/v1/orchestrator/features/{id}/run
- Запуск выполнения фичи
- Ответ: run_id, state

GET /api/v1/orchestrator/graph/{run_id}/status
- Получение статуса запуска графа
- Ответ: run_id, graph, status, last_checkpoint

### Index

GET /api/v1/index/symbol
- Получение информации о символе
- Параметры: name

GET /api/v1/index/calls
- Получение информации о вызовах функции
- Параметры: name

### Tokens

GET /admin/tokens
- Получение сводки расхода токенов
- Ответ: сводка по ролям, моделям, дням

### Stream

GET /api/v1/stream/events
- Получение потока событий в реальном времени через SSE
- Ответ: поток событий job_started, job_finished, error, index_updated, doc_updated, llm_call_end

### Logs

GET /api/v1/logs/tail
- Получение последних записей логов (fallback для UI)
- Параметры: limit (по умолчанию 100)
- Ответ: массив записей логов

### Maintainer

POST /api/v1/maintainer/intent
- Генерация intent из естественного языка
- Параметры: nl_text
- Ответ: intent_json, issues, suggestions

POST /api/v1/maintainer/plan
- Генерация плана выполнения из intent
- Параметры: intent_json
- Ответ: dag, package_contract

### Logs

GET /api/v1/logs/tail
- Получение последних записей логов (fallback для UI)
- Параметры: limit (по умолчанию 100)

### Stream

GET /api/v1/stream/events
- SSE поток событий
- События: job_started, job_finished, error, index_updated, doc_updated, llm_call_end

### Maintainer

POST /api/v1/maintainer/intent
- Генерация intent из естественного языка
- Параметры: nl_text
- Ответ: intent_json, issues, suggestions

POST /api/v1/maintainer/plan
- Генерация плана выполнения из intent
- Параметры: intent_json
- Ответ: dag, package_contract