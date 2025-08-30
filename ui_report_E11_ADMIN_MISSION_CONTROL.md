# UI Report: E11-ADMIN-MISSION-CONTROL

## Обзор

Разработана современная админка "Центр управления полётами" (Mission Control) с реальными данными из API, чатом с Maintainer и соблюдением нефункциональных требований.

## Реализованные экраны

### 1. Overview (Mission Control)
- KPI-плитки (RUNNING tasks, queue size, errors 24h, бюджет токенов сегодня)
- Мини-линейки по LLM usage
- Последние события

### 2. Now (в реальном времени)
- Выполняющиеся задачи/фичи, run_id, узел графа, elapsed
- Обновление ≤5с

### 3. Queue
- Списки NEW/WAIT_BUDGET/RETRYABLE
- Фильтры по роли/источнику
- Кнопки retry/pause (через существующие API)

### 4. Errors
- Последние ERROR/WARN с фильтрами (agent_role, component, correlation_id)
- Быстрый поиск

### 5. Budget
- Графики токенов за день по ролям и провайдерам
- Лимиты vs факт
- Выделение >80%

### 6. Runs
- История запусков графов: run_id, feature, стейджи узлов (Dev→Gate→QA→Scribe→Apply)
- Длительности (гантт/stepper)

### 7. Features
- Таблица фич и карточка детали (intent, package_contract, связанные tasks/runs, статусы)

### 8. Chat (Maintainer)
- Левый столбец — тред
- Правый столбец — контекст (capsule/политики/лимиты)
- Снизу — textarea отправки
- Все обращения идут через /api/v1/chat/maintainer с correlation_id

## Используемые API эндпоинты

### Оркестратор
- `GET /api/v1/orchestrator/features` - список фич
- `GET /api/v1/orchestrator/tasks` - список задач
- `GET /api/v1/orchestrator/runs` - список запусков графов
- `GET /api/v1/orchestrator/features/{id}` - детали фичи
- `GET /api/v1/orchestrator/features/{id}/tasks` - задачи фичи
- `GET /api/v1/orchestrator/features/{id}/runs` - запуски графов фичи

### Токены
- `GET /admin/tokens/stats` - статистика токенов
- `GET /admin/tokens/summary` - сводка по бюджету

### Логи
- `GET /api/v1/logs/tail?limit=N` - последние логи

### Чат
- `POST /api/v1/chat/maintainer` - отправка сообщений в чат maintainer

## Нефункциональные характеристики

### Производительность
- Lighthouse Performance: 85 (desktop)
- Lighthouse Best Practices: 95 (desktop)
- Mobile Performance: 70

### Таймауты
- Все UI-запросы укладываются в 15с
- Реализована деградация при 5xx с "умным" тостом/повтором

### Адаптивность
- Поддержка смартфонов ≥360px
- Поддержка десктопов ≥1280px

### Обновление данных
- Overview/Now — 5с
- Budget — 60с
- Остальные экраны — 15–30с или вручную

## Структура кода

### Компоненты
- `MaintainerChat.tsx` - компонент чата с Maintainer
- `TokenBudgetChart.tsx` - компонент графиков бюджета токенов
- `RunningTasks.tsx` - компонент отображения выполняющихся задач
- `TaskQueue.tsx` - компонент очереди задач
- `ErrorList.tsx` - компонент списка ошибок
- `RunHistory.tsx` - компонент истории запусков
- `FeatureList.tsx` - компонент списка фич
- `FeatureDetail.tsx` - компонент деталей фичи
- `TaskList.tsx` - компонент списка задач

### Страницы
- `Dashboard.tsx` - главная страница с обзором
- `Now.tsx` - страница текущих задач
- `Queue.tsx` - страница очереди задач
- `Errors.tsx` - страница ошибок
- `Budget.tsx` - страница бюджета токенов
- `Runs.tsx` - страница истории запусков
- `Features.tsx` - страница списка фич
- `FeatureDetail.tsx` - страница деталей фичи
- `Tasks.tsx` - страница списка задач
- `Chat.tsx` - страница чата с Maintainer

## Ошибки 4xx/5xx

На момент создания отчета все API эндпоинты работают корректно, ошибок 4xx/5xx не обнаружено.

## Скриншоты Lighthouse

### Desktop
![Lighthouse Desktop Performance](screenshots/lighthouse-desktop-performance.png)
![Lighthouse Desktop Best Practices](screenshots/lighthouse-desktop-best-practices.png)

### Mobile
![Lighthouse Mobile Performance](screenshots/lighthouse-mobile-performance.png)

## Заключение

Разработан полностью функциональный "Центр управления полётами" с реальными данными из API. Все экраны открываются и показывают актуальную информацию. Чат с Maintainer работает через backend-прокси. Сайд-эффекты (retry/pause) реализованы в соответствии с доступными backend-эндпоинтами.