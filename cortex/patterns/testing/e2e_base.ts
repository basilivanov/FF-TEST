// Базовые классы для E2E тестирования FeatureFactory
import { test as base, expect, Page, Browser, BrowserContext } from '@playwright/test'
import { randomUUID } from 'crypto'

// Типы для тестовых данных
export interface TestContext {
  correlationId: string
  testUser: string
  baseURL: string
  apiKey?: string
}

export interface FFPage {
  // Навигация
  goto(path: string): Promise<void>
  
  // Ожидания
  waitForSystemReady(): Promise<void>
  waitForAgentsOnline(): Promise<void>
  
  // Проверки статуса
  checkHealthStatus(): Promise<boolean>
  checkAgentsStatus(): Promise<{ working: number, total: number }>
  
  // Работа с фичами
  createFeature(title: string): Promise<string>
  getFeatureStatus(id: string): Promise<string>
}

// Расширенный тест с контекстом FeatureFactory
export const test = base.extend<TestContext>({
  correlationId: async ({}, use) => {
    const correlationId = `e2e_${randomUUID().slice(0, 8)}`
    await use(correlationId)
  },
  
  testUser: async ({}, use) => {
    const testUser = `playwright_user_${Date.now()}`
    await use(testUser)
  },
  
  baseURL: async ({}, use) => {
    const baseURL = process.env.FF_API_BASE_URL || 'http://localhost:8081'
    await use(baseURL)
  }
})

// Page Object для FeatureFactory
export class FFPageObject implements FFPage {
  constructor(private page: Page, private context: TestContext) {}

  async goto(path: string): Promise<void> {
    const url = `${this.context.baseURL}${path.startsWith('/') ? path : '/' + path}`
    await this.page.goto(url)
    
    // Устанавливаем correlation ID в локальное хранилище
    await this.page.evaluate((correlationId) => {
      localStorage.setItem('correlation_id', correlationId)
    }, this.context.correlationId)
  }

  async waitForSystemReady(): Promise<void> {
    // Ждем готовности системы по индикатору на Dashboard
    await this.page.waitForSelector('[data-testid="system-health-indicator"]', { 
      state: 'visible',
      timeout: 30_000 
    })
    
    // Проверяем, что индикатор показывает "Ready"
    await expect(this.page.locator('[data-testid="system-health-indicator"]'))
      .toContainText('Ready')
  }

  async waitForAgentsOnline(): Promise<void> {
    // Ждем, что все агенты онлайн
    await this.page.waitForFunction(
      () => {
        const indicator = document.querySelector('[data-testid="agents-status"]')
        return indicator?.textContent?.includes('Online')
      },
      { timeout: 60_000 }
    )
  }

  async checkHealthStatus(): Promise<boolean> {
    try {
      const healthElement = await this.page.locator('[data-testid="system-health-status"]')
      const status = await healthElement.textContent()
      return status?.includes('🟢') || status?.includes('Ready') || false
    } catch {
      return false
    }
  }

  async checkAgentsStatus(): Promise<{ working: number, total: number }> {
    const statusText = await this.page
      .locator('[data-testid="agents-working-count"]')
      .textContent()
    
    const match = statusText?.match(/(\d+)\/(\d+)/)
    if (match) {
      return {
        working: parseInt(match[1], 10),
        total: parseInt(match[2], 10)
      }
    }
    
    return { working: 0, total: 0 }
  }

  async createFeature(title: string): Promise<string> {
    // Переходим на страницу создания фичи
    await this.goto('/features')
    await this.page.click('[data-testid="create-feature-button"]')
    
    // Заполняем форму
    await this.page.fill('[data-testid="feature-title-input"]', title)
    await this.page.fill('[data-testid="feature-description-input"]', `E2E test feature: ${title}`)
    
    // Отправляем форму
    await this.page.click('[data-testid="submit-feature-button"]')
    
    // Ждем редиректа и получаем ID фичи
    await this.page.waitForURL(/\/features\/(\d+)/)
    const url = this.page.url()
    const featureId = url.match(/\/features\/(\d+)/)?.[1] || ''
    
    return featureId
  }

  async getFeatureStatus(id: string): Promise<string> {
    await this.goto(`/features/${id}`)
    
    const statusBadge = await this.page.locator('[data-testid="feature-status-badge"]')
    const status = await statusBadge.textContent()
    
    return status?.trim() || 'UNKNOWN'
  }
}

// Фикстуры для тестов
export const ffTest = test.extend<{ ffPage: FFPageObject }>({
  ffPage: async ({ page, correlationId, testUser, baseURL }, use) => {
    const context: TestContext = { correlationId, testUser, baseURL }
    const ffPage = new FFPageObject(page, context)
    await use(ffPage)
  }
})

// Вспомогательные функции
export async function setupTestEnvironment(page: Page, context: TestContext) {
  // Мокаем внешние вызовы если нужно
  await page.route('**/api/external/**', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'mocked', correlation_id: context.correlationId })
    })
  })
  
  // Устанавливаем тестовые заголовки
  await page.setExtraHTTPHeaders({
    'X-Correlation-ID': context.correlationId,
    'X-Test-User': context.testUser
  })
}

// Проверки состояния системы
export const systemChecks = {
  async isHealthy(page: Page): Promise<boolean> {
    try {
      const response = await page.request.get('/api/health')
      return response.status() === 200
    } catch {
      return false
    }
  },
  
  async areAgentsOnline(page: Page): Promise<boolean> {
    try {
      const response = await page.request.get('/api/agents/status')
      const data = await response.json()
      return data.status === 'ok' && data.working_providers > 0
    } catch {
      return false
    }
  }
}

export { expect }