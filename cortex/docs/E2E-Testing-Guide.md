# E2E Testing Guide

## Обзор

Этот документ описывает подход к end-to-end тестированию пользовательского интерфейса Feature Factory Admin UI.

## Стек тестирования

- **Playwright** - фреймворк для E2E тестирования
- **TypeScript** - язык программирования для тестов
- **Jest** - фреймворк для unit тестирования (для вспомогательных функций)

## Структура тестов

Тесты организованы по следующей структуре:

```
e2e-tests/
  ui.test.ts          # Основные E2E тесты UI
  fixtures/           # Фикстуры для тестов
  utils/              # Вспомогательные функции
  pages/              # Page Object Model классы
performance-tests/
  ui-performance.test.ts  # Тесты производительности UI
security-tests/
  ui-security.test.ts     # Тесты безопасности UI
accessibility-tests/
  ui-accessibility.test.ts  # Тесты доступности UI
compatibility-tests/
  ui-compatibility.test.ts  # Тесты совместимости UI
```

## Page Object Model

Для упрощения написания и поддержки тестов используется паттерн Page Object Model. Каждая страница приложения имеет соответствующий класс, который инкапсулирует локаторы элементов и методы взаимодействия с ними.

### Пример Page Object

```typescript
// e2e-tests/pages/DashboardPage.ts
import { Page } from '@playwright/test';

export class DashboardPage {
  constructor(private page: Page) {}

  async navigate() {
    await this.page.goto('/dashboard');
  }

  async getTitle() {
    return await this.page.textContent('h1');
  }

  async getSystemHealthCard() {
    return this.page.locator('[data-testid="system-health-card"]');
  }

  async clickRefreshButton() {
    await this.page.click('[data-testid="refresh-button"]');
  }
}
```

## Написание тестов

### Основные принципы

1. **Тестирование пользовательских сценариев**
   - Тесты должны отражать реальные сценарии использования приложения
   - Каждый тест должен представлять законченный пользовательский путь

2. **Изоляция тестов**
   - Каждый тест должен быть независимым
   - Тесты не должны зависеть друг от друга
   - Используйте фикстуры для подготовки данных

3. **Читаемость**
   - Используйте описательные имена для тестов
   - Структурируйте тесты с помощью describe блоков
   - Комментируйте сложные шаги

### Пример теста

```typescript
// e2e-tests/ui.test.ts
import { test, expect } from '@playwright/test';

test.describe('Feature Factory Admin UI', () => {
  test('should allow user to create a new feature', async ({ page }) => {
    // Arrange
    await page.goto('/');
    await page.fill('[name="username"]', 'admin');
    await page.fill('[name="password"]', 'admin');
    await page.click('button[type="submit"]');
    
    // Act
    await page.click('text=Features');
    await page.click('button:has-text("Создать фичу")');
    await page.fill('input[name="title"]', 'Новая фича');
    await page.fill('textarea[name="description"]', 'Описание новой фичи');
    await page.click('button:has-text("Создать")');
    
    // Assert
    await expect(page).toHaveURL(/\/features\/\d+/);
    await expect(page.getByText('Новая фича')).toBeVisible();
  });
});
```

## Типы тестов

### Функциональные тесты

Функциональные тесты проверяют корректность работы всех функций приложения.

#### Примеры функциональных тестов:
- Авторизация и навигация
- Создание, редактирование и удаление фич
- Запуск и мониторинг задач
- Просмотр логов и статистики
- Управление документацией

### Регрессионные тесты

Регрессионные тесты проверяют, что новые изменения не сломали существующую функциональность.

#### Примеры регрессионных тестов:
- Проверка всех экранов после обновления
- Проверка всех форм и валидаций
- Проверка всех пользовательских сценариев

### Интеграционные тесты

Интеграционные тесты проверяют взаимодействие между различными частями приложения.

#### Примеры интеграционных тестов:
- Тестирование API эндпоинтов
- Проверка интеграции с бэкендом
- Тестирование потоков данных

## Запуск тестов

### Запуск всех E2E тестов

```bash
npm run test:e2e
```

### Запуск тестов в режиме watch

```bash
npm run test:e2e -- --headed
```

### Запуск конкретного теста

```bash
npm run test:e2e -- ui.test.ts
```

### Запуск тестов в разных браузерах

```bash
# Chrome (по умолчанию)
npm run test:e2e -- --browser=chromium

# Firefox
npm run test:e2e -- --browser=firefox

# Safari
npm run test:e2e -- --browser=webkit
```

## Конфигурация

### Playwright конфигурация

Конфигурация Playwright находится в файле `playwright.config.ts`:

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e-tests',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    actionTimeout: 0,
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      timeout: 60 * 1000,
      retries: 3,
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  outputDir: 'test-results/',
});
```

## Лучшие практики

### 1. Использование Page Object Model

```typescript
// Плохо
test('should create feature', async ({ page }) => {
  await page.goto('/features');
  await page.click('button:has-text("Создать фичу")');
  await page.fill('input[name="title"]', 'Моя фича');
  await page.click('button[type="submit"]');
  await expect(page.getByText('Моя фича')).toBeVisible();
});

// Хорошо
test('should create feature', async ({ page }) => {
  const featuresPage = new FeaturesPage(page);
  const featureForm = new FeatureForm(page);
  
  await featuresPage.navigate();
  await featuresPage.clickCreateFeatureButton();
  await featureForm.fillTitle('Моя фича');
  await featureForm.submit();
  
  const featureDetailPage = new FeatureDetailPage(page);
  await expect(featureDetailPage.getTitle()).toEqual('Моя фича');
});
```

### 2. Использование фикстур

```typescript
// e2e-tests/fixtures/user.ts
import { test as baseTest } from '@playwright/test';

export const test = baseTest.extend({
  user: async ({ page }, use) => {
    // Создаем тестового пользователя
    const user = {
      username: 'testuser',
      password: 'testpass',
      email: 'test@example.com'
    };
    
    // Подготавливаем данные в базе
    // ...
    
    await use(user);
    
    // Очищаем данные после теста
    // ...
  },
});

export { expect } from '@playwright/test';
```

### 3. Обработка асинхронных операций

```typescript
// Плохо
test('should show loading state', async ({ page }) => {
  await page.click('button:has-text("Загрузить данные")');
  await expect(page.getByText('Загружается...')).toBeVisible();
  // Плохо, потому что не ждем завершения загрузки
  await expect(page.getByText('Данные загружены')).toBeVisible();
});

// Хорошо
test('should show loading state', async ({ page }) => {
  await page.click('button:has-text("Загрузить данные")');
  await expect(page.getByText('Загружается...')).toBeVisible();
  await page.waitForSelector('text=Данные загружены');
  await expect(page.getByText('Данные загружены')).toBeVisible();
});
```

### 4. Использование ожиданий

```typescript
// Плохо
await page.click('button');
await page.click('next-button');

// Хорошо
await page.click('button');
await page.waitForLoadState('networkidle');
await page.click('next-button');
await page.waitForSelector('.result-loaded');
```

## Отладка тестов

### Просмотр отчетов

После запуска тестов генерируется HTML отчет:

```bash
npm run test:e2e
# Открываем отчет в браузере
npx playwright show-report
```

### Просмотр трассировок

Playwright генерирует трассировки для тестов, которые можно просмотреть:

```bash
# Просмотр трассировки последнего теста
npx playwright show-trace test-results/dashboard-page-chromium/trace.zip
```

### Запуск тестов с отладкой

```bash
# Запуск тестов с открытием браузера
npm run test:e2e -- --headed

# Запуск тестов с паузой на каждом шаге
npm run test:e2e -- --debug

# Запуск тестов с записью видео
npm run test:e2e -- --record-video
```

## CI/CD интеграция

### GitHub Actions_workflow

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Install Playwright browsers
      run: npx playwright install --with-deps
      
    - name: Start dev server
      run: npm run dev &
      
    - name: Wait for server to start
      run: sleep 10
      
    - name: Run E2E tests
      run: npm run test:e2e
      
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: test-results/
        
    - name: Upload HTML report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: html-report
        path: playwright-report/
```

## Производительность тестов

### Оптимизация времени выполнения

1. **Параллельный запуск**
   - Используйте `fullyParallel: true` в конфигурации
   - Разделяйте тесты на независимые наборы

2. **Кэширование данных**
   - Используйте фикстуры для подготовки данных
   - Переиспользуйте подготовленные данные между тестами

3. **Оптимизация селекторов**
   - Используйте data-testid атрибуты
   - Избегайте сложных CSS селекторов

### Мониторинг производительности

```typescript
// e2e-tests/performance.test.ts
import { test, expect } from '@playwright/test';

test('should load dashboard within acceptable time', async ({ page }) => {
  const startTime = Date.now();
  await page.goto('/dashboard');
  const loadTime = Date.now() - startTime;
  
  expect(loadTime).toBeLessThan(3000); // 3 секунды
  
  // Проверяем, что основные элементы загружены
  await expect(page.getByText('System Health')).toBeVisible();
});
```

## Безопасность тестов

### Тестирование уязвимостей

1. **XSS атаки**
   ```typescript
   test('should prevent XSS in chat messages', async ({ page }) => {
     await page.goto('/chat');
     await page.fill('textarea', '<script>alert("XSS")</script>');
     await page.click('button:has-text("Send")');
     
     // Проверяем, что скрипт не выполнился
     await expect(page.getByText('<script>alert("XSS")</script>')).toBeVisible();
     // А не alert
   });
   ```

2. **CSRF атаки**
   ```typescript
   test('should have CSRF protection', async ({ page }) => {
     // Проверяем, что формы защищены CSRF токенами
     await page.goto('/settings');
     await page.click('button:has-text("Редактировать")');
     
     const csrfTokenInput = await page.$('input[name="_csrf_token"]');
     expect(csrfTokenInput).not.toBeNull();
   });
   ```

## Доступность тестов

### Тестирование доступности

1. **Навигация с клавиатуры**
   ```typescript
   test('should be navigable with keyboard', async ({ page }) => {
     await page.goto('/dashboard');
     
     // Проверяем, что элементы фокусируются в правильном порядке
     await page.keyboard.press('Tab');
     await expect(page.locator(':focus')).toHaveText('Dashboard');
     
     await page.keyboard.press('Tab');
     await expect(page.locator(':focus')).toHaveRole('button');
   });
   ```

2. **ARIA атрибуты**
   ```typescript
   test('should have proper ARIA attributes', async ({ page }) => {
     await page.goto('/features');
     
     const table = await page.$('table');
     const role = await table?.getAttribute('role');
     expect(role).toBe('table');
   });
   ```

## Совместимость тестов

### Тестирование в разных браузерах

```typescript
// playwright.config.ts
projects: [
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'] },
  },
  {
    name: 'firefox',
    use: { ...devices['Desktop Firefox'] },
  },
  {
    name: 'webkit',
    use: { ...devices['Desktop Safari'] },
  },
  {
    name: 'Mobile Chrome',
    use: { ...devices['Pixel 5'] },
  },
  {
    name: 'Mobile Safari',
    use: { ...devices['iPhone 12'] },
  },
],
```

## Troubleshooting

### Частые проблемы

1. **Тесты падают из-за таймингов**
   - Используйте `waitForSelector` и `waitForLoadState`
   - Увеличьте таймауты для медленных операций

2. **Тесты нестабильны**
   - Убедитесь, что тесты изолированы
   - Используйте фикстуры для подготовки данных
   - Избегайте зависимости от внешних сервисов

3. **Проблемы с селекторами**
   - Используйте data-testid атрибуты
   - Избегайте сложных CSS селекторов
   - Обновляйте селекторы при изменении UI

## Полезные ресурсы

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Page Object Model](https://playwright.dev/docs/pom)
- [Test Fixtures](https://playwright.dev/docs/test-fixtures)
- [Debugging Tests](https://playwright.dev/docs/debug)
- [CI/CD Integration](https://playwright.dev/docs/ci)