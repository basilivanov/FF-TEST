# Feature Factory

Feature Factory - это платформа для автоматической генерации и управления бизнес-фичами с помощью LLM.

## Обзор

Feature Factory предоставляет инструменты для:
- Автоматической генерации кода фич на основе описания на естественном языке
- Управления жизненным циклом фич через оркестрацию
- Мониторинга и логирования процессов
- Веб-интерфейса администратора для управления системой

## Архитектура

### Стек технологий

- **Бэкенд**: Python 3.12, FastAPI, SQLite, SQLAlchemy, Alembic
- **LLM**: LiteLLM для маршрутизации запросов между провайдерами
- **Оркестрация**: LangGraph для управления графами выполнения
- **Фронтенд**: Vite, React, TypeScript, Tailwind CSS, shadcn/ui
- **Инфраструктура**: Nginx для проксирования и статических файлов

### Компоненты

1. **Оркестратор** - управляет жизненным циклом фич
2. **Агенты** - генерируют код, тестируют, документируют фичи
3. **Индексер** - индексирует код для быстрой навигации LLM
4. **Веб-интерфейс** - админка для управления системой
5. **Логирование** - централизованное логирование всех процессов

## Установка

### Предварительные требования

- Python 3.12
- Node.js 16+
- SQLite 3
- Nginx

### Установка бэкенда

```bash
# Клонирование репозитория
git clone <repository-url>
cd feature-factory

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Инициализация базы данных
alembic upgrade head
```

### Установка фронтенда

```bash
cd app/ui
npm install
```

## Запуск

### Запуск бэкенда

```bash
# Активация виртуального окружения
source .venv/bin/activate

# Запуск сервера (тестовое окружение)
python -m app.main

# Запуск сервера (продакшен окружение)
ENV=PROD python -m app.main
```

### Запуск фронтенда в режиме разработки

```bash
cd app/ui
npm run dev
```

### Сборка фронтенда для продакшена

```bash
cd app/ui
npm run build
```

## Веб-интерфейс

Веб-интерфейс администратора доступен по адресу:
- Тест: https://etl-tst.chococraft.ru/admin
- Продакшен: https://etl.chococraft.ru/admin

### Учетные данные для доступа

- Логин: ops
- Пароль: ops123

### Функции веб-интерфейса

- **Dashboard** - обзор состояния системы
- **Features** - управление фичами
- **Tasks** - управление задачами
- **Runs** - мониторинг запусков графов
- **Logs** - просмотр логов в реальном времени
- **Tokens** - мониторинг расхода токенов LLM
- **Docs** - управление документацией
- **Settings** - настройки системы
- **Chat** - взаимодействие с системой на естественном языке

## API

### Основные эндпоинты

- `POST /api/v1/maintainer/intent` - генерация интента из NL
- `POST /api/v1/maintainer/plan` - генерация плана из интента
- `POST /api/v1/orchestrator/features` - создание фичи
- `POST /api/v1/orchestrator/features/{id}/plan` - планирование фичи
- `POST /api/v1/orchestrator/features/{id}/run` - запуск фичи
- `GET /api/v1/orchestrator/graph/{run_id}/status` - статус графа
- `GET /api/v1/stream/events` - поток событий (SSE)
- `GET /api/v1/logs/tail` - последние записи логов
- `GET /admin/tokens` - статистика токенов

### Health Checks

- `GET /api/v1/health` - общее состояние
- `GET /api/v1/health/live` - liveness probe
- `GET /api/v1/health/ready` - readiness probe
- `GET /api/v1/health/deps` - проверка зависимостей

## Конфигурация

### Переменные окружения

Основные переменные окружения находятся в файлах:
- `.env` - основная конфигурация
- `configs/feature-factory-test.env` - тестовое окружение
- `configs/feature-factory-prod.env` - продакшен окружение

### Конфигурация Nginx

Конфигурационные файлы Nginx:
- `configs/nginx/etl-tst.chococraft.ru` - тест
- `configs/nginx/etl.chococraft.ru` - продакшен

## Документация

Подробная документация находится в директории `docs/`:

- `Architecture.md` - архитектура системы
- `UI-000.md` - спецификация веб-интерфейса
- `Commands-UI-000.md` - команды веб-интерфейса
- `API-Orchestrator-001.md` - спецификация API оркестратора
- `API-Maintainer-001.md` - спецификация API maintainer
- `Logging-001.md` - стандарт логирования
- `Policy-LLM-000.md` - политики использования LLM
- `UI-Development-Guide.md` - руководство по разработке UI
- `UI-Deployment-Guide.md` - руководство по деплою UI
- `UI-Testing-Guide.md` - руководство по тестированию UI
- `UI-Components.md` - описание компонентов UI
- `UI-Backend-Integration.md` - интеграция UI с бэкендом
- `E2E-Testing-Guide.md` - руководство по end-to-end тестированию

## Тестирование

### Запуск тестов бэкенда

```bash
python -m pytest tests/
```

### Запуск тестов фронтенда

```bash
cd app/ui
npm test
```

### Coverage

```bash
# Бэкенд
python -m pytest tests/ --cov=app

# Фронтенд
cd app/ui
npm test -- --coverage
```

## Деплой

### Деплой бэкенда

Используйте systemd сервисы:
- `configs/feature-factory-test.service` - тест
- `configs/feature-factory-prod.service` - продакшен

### Деплой фронтенда

```bash
sudo /opt/feature-factory/scripts/deploy_ui.sh
```

## Мониторинг

### Логи

Логи доступны в директории `logs/` и через веб-интерфейс.

### Метрики

Метрики доступны через эндпоинты health check.

## Contributing

1. Форкните репозиторий
2. Создайте ветку для вашей фичи (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Запушьте ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## Лицензия

Уточняется

## Контакты

Уточняется