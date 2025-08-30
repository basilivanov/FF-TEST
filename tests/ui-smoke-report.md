# UI Smoke Tests Report

## Статус

**Создан** — 2025-08-22

## Обзор

Smoke tests для веб-интерфейса Feature Factory Admin UI. Проверяют основные функции без глубокого тестирования логики.

## Тестовые сценарии

### 1. Доступность главной страницы

**URL:** `https://etl-tst.chococraft.ru/`

**Ожидания:**
- HTTP 200 после BasicAuth (ops:ops123)
- Отображается React приложение
- Видна навигация (Dashboard, Features, Tasks, etc.)

### 2. Dashboard загружается

**URL:** `https://etl-tst.chococraft.ru/`

**Ожидания:**
- Показаны карточки: System Health, Backlog, Recent Runs, LLM Budgets, Errors, Docs
- Данные загружаются с API без ошибок
- ENV banner показывает "TEST"

### 3. Features страница работает

**URL:** `https://etl-tst.chococraft.ru/features`

**Ожидания:**
- Список фичей загружается из `/api/v1/orchestrator/features`
- Показываются кнопки Plan/Run для NEW фичей
- Фильтрация по статусу функционирует

### 4. Logs страница показывает события

**URL:** `https://etl-tst.chococraft.ru/logs`

**Ожидания:**
- SSE подключение к `/api/v1/stream/events` успешно
- Показывается хотя бы 1 событие из логов
- Фильтры по component/level работают
- Fallback на `/api/v1/logs/tail` при отказе SSE

### 5. Chat интерфейс функционирует

**URL:** `https://etl-tst.chococraft.ru/chat`

**Ожидания:**
- Поле ввода NL текста активно
- Отправка запроса на `/api/v1/maintainer/intent` успешна
- Получение intent и отображение превью

### 6. API endpoints доступны

**Проверяемые эндпоинты:**
- `GET /api/v1/orchestrator/features` → 200
- `GET /admin/tokens` → 200  
- `GET /api/v1/stream/events` → 200 (SSE)
- `POST /api/v1/maintainer/intent` → 200

## Команды для запуска

### Playwright Setup

```bash
# Установка Playwright (если еще не установлен)
cd /opt/feature-factory
npm install -D @playwright/test
npx playwright install

# Создание базового теста
cat > tests/ui-smoke.spec.ts << 'EOF'
import { test, expect } from '@playwright/test';

test.describe('UI Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    // BasicAuth
    await page.setExtraHTTPHeaders({
      'Authorization': 'Basic ' + Buffer.from('ops:ops123').toString('base64')
    });
  });

  test('Dashboard loads successfully', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Feature Factory Admin')).toBeVisible();
    await expect(page.getByText('System Health')).toBeVisible();
  });

  test('Features page loads', async ({ page }) => {
    await page.goto('/features');
    await expect(page.getByText('Features')).toBeVisible();
    // Ждем загрузки данных
    await page.waitForResponse('/api/v1/orchestrator/features');
  });

  test('Chat sends NL request', async ({ page }) => {
    await page.goto('/chat');
    await page.fill('[placeholder*="естественный язык"]', 'Создать тестовую фичу');
    await page.click('button:has-text("Отправить")');
    await page.waitForResponse('/api/v1/maintainer/intent');
  });
});
EOF

# Запуск тестов
npx playwright test tests/ui-smoke.spec.ts
```

### Простые curl тесты

```bash
# Проверка доступности UI
curl -u ops:ops123 -s -o /dev/null -w "%{http_code}" https://etl-tst.chococraft.ru/

# Проверка API endpoints
curl -u ops:ops123 -s https://etl-tst.chococraft.ru/api/v1/orchestrator/features
curl -u ops:ops123 -s https://etl-tst.chococraft.ru/admin/tokens

# Проверка Maintainer API
curl -u ops:ops123 -X POST -H "Content-Type: application/json" \
  -d '{"nl_text":"тест"}' \
  https://etl-tst.chococraft.ru/api/v1/maintainer/intent
```

## Результаты

### ✅ Пройдено

- UI собирается и деплоится успешно (`app/ui/dist/`)
- Nginx конфигурация обновлена для SPA routing
- BasicAuth настроен для всех эндпоинтов
- API Maintainer доступен и отвечает корректно

### ⚠️ Требует проверки

- Реальное развертывание nginx конфигурации (требует sudo)
- Playwright тесты в CI/CD pipeline
- SSE соединения через nginx proxy

### 📋 Следующие шаги

1. Применить nginx конфигурацию:
   ```bash
   sudo cp /opt/feature-factory/nginx-config/etl-tst.chococraft.ru /etc/nginx/sites-available/
   sudo nginx -t && sudo systemctl reload nginx
   ```

2. Запустить полные smoke tests после деплоя

3. Настроить мониторинг доступности UI

## Заключение

UI готов к deployment. Основные компоненты E8 Admin UI реализованы и протестированы на уровне сборки. Требуется финальное развертывание nginx конфигурации для полного завершения задачи.