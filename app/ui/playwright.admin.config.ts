import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30 * 1000,
  expect: { timeout: 5000 },
  reporter: 'line',
  use: {
    baseURL: process.env.PW_BASE_URL || 'https://etl-tst.chococraft.ru',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    ignoreHTTPSErrors: true,
    headless: true,
    launchOptions: {
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    },
    httpCredentials: {
      username: process.env.PW_HTTP_USER || 'ops',
      password: process.env.PW_HTTP_PASS || 'ops123',
    },
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
