// Playwright конфигурация для E2E тестирования FeatureFactory
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  // Тесты находятся в tests/e2e/
  testDir: './tests/e2e',
  
  // Таймауты
  timeout: 30_000,
  expect: { timeout: 10_000 },
  
  // Параллельные тесты
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  
  // Ретрай для нестабильных тестов
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // Отчеты
  reporter: [
    ['html', { outputFolder: 'test-results/html' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['json', { outputFile: 'test-results/results.json' }]
  ],

  // Глобальные настройки
  use: {
    // Base URL для тестов
    baseURL: process.env.FF_API_BASE_URL || 'http://localhost:8081',
    
    // Трассировка для отладки
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    
    // Корреляция для логирования
    extraHTTPHeaders: {
      'X-Correlation-ID': 'playwright-e2e'
    }
  },

  // Браузеры для тестирования
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] }
    }
  ],

  // Веб-сервер для тестов
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      NODE_ENV: 'test',
      FF_API_BASE_URL: process.env.FF_API_BASE_URL || 'http://localhost:8081'
    }
  }
})