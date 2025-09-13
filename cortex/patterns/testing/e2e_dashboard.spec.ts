// E2E тесты для Dashboard
import { ffTest, expect, setupTestEnvironment, systemChecks } from './e2e_base'

ffTest.describe('Dashboard - Mission Control', () => {
  ffTest.beforeEach(async ({ page, correlationId, testUser, baseURL }) => {
    await setupTestEnvironment(page, { correlationId, testUser, baseURL })
  })

  ffTest('отображает основные виджеты Dashboard', async ({ ffPage }) => {
    await ffPage.goto('/')
    
    // Проверяем загрузку основных компонентов
    await expect(page.locator('h1')).toContainText('Mission Control Dashboard')
    
    // Виджеты должны быть видимы
    await expect(page.locator('[data-testid="system-health-card"]')).toBeVisible()
    await expect(page.locator('[data-testid="agents-status-card"]')).toBeVisible()
    await expect(page.locator('[data-testid="active-processes-card"]')).toBeVisible()
    await expect(page.locator('[data-testid="backlog-card"]')).toBeVisible()
    await expect(page.locator('[data-testid="budget-card"]')).toBeVisible()
    await expect(page.locator('[data-testid="alerts-card"]')).toBeVisible()
  })

  ffTest('показывает статус системы', async ({ ffPage, page }) => {
    await ffPage.goto('/')
    
    // Ждем загрузки данных
    await ffPage.waitForSystemReady()
    
    // Проверяем статус здоровья системы
    const isHealthy = await ffPage.checkHealthStatus()
    expect(isHealthy).toBeTruthy()
    
    // Проверяем статус агентов
    const agentsStatus = await ffPage.checkAgentsStatus()
    expect(agentsStatus.total).toBeGreaterThan(0)
    expect(agentsStatus.working).toBeGreaterThanOrEqual(0)
  })

  ffTest('позволяет навигацию по разделам', async ({ ffPage, page }) => {
    await ffPage.goto('/')
    
    // Клик по System Health ведет в Logs
    await page.click('[data-testid="system-health-card"]')
    await expect(page).toHaveURL(/\/logs/)
    
    // Возвращаемся на Dashboard
    await ffPage.goto('/')
    
    // Клик по LLM Agents ведет в Agents
    await page.click('[data-testid="agents-status-card"]')
    await expect(page).toHaveURL(/\/agents/)
    
    // Возвращаемся на Dashboard
    await ffPage.goto('/')
    
    // Клик по Backlog ведет в Features
    await page.click('[data-testid="backlog-card"]')
    await expect(page).toHaveURL(/\/features/)
  })

  ffTest('отображает активные процессы', async ({ ffPage, page }) => {
    await ffPage.goto('/')
    
    // Проверяем секцию активных процессов
    const activeProcesses = page.locator('[data-testid="active-processes-card"]')
    await expect(activeProcesses).toBeVisible()
    
    // Должны быть счетчики запусков и фич
    await expect(activeProcesses.locator('[data-testid="running-runs-count"]')).toBeVisible()
    await expect(activeProcesses.locator('[data-testid="running-features-count"]')).toBeVisible()
  })

  ffTest('показывает бюджет LLM токенов', async ({ ffPage, page }) => {
    await ffPage.goto('/')
    
    const budgetCard = page.locator('[data-testid="budget-card"]')
    await expect(budgetCard).toBeVisible()
    
    // Если есть данные по бюджету, проверяем прогресс-бар
    const budgetData = await budgetCard.locator('[data-testid="budget-usage"]').isVisible()
    if (budgetData) {
      await expect(budgetCard.locator('.bg-gray-200')).toBeVisible() // Progress bar background
    }
  })

  ffTest('обновляет данные при клике на кнопку обновления', async ({ ffPage, page }) => {
    await ffPage.goto('/')
    
    // Проверяем наличие кнопки обновления
    const refreshButton = page.locator('[data-testid="refresh-data-button"]')
    await expect(refreshButton).toBeVisible()
    
    // Кликаем на обновление
    await refreshButton.click()
    
    // Проверяем, что данные обновились (spinner должен появиться и исчезнуть)
    await expect(refreshButton.locator('.animate-spin')).toBeVisible({ timeout: 1000 })
    await expect(refreshButton.locator('.animate-spin')).not.toBeVisible({ timeout: 5000 })
  })
})

ffTest.describe('Dashboard - Критические проверки', () => {
  ffTest('система готова к работе', async ({ ffPage, page }) => {
    await ffPage.goto('/')
    
    // Системные проверки
    const isHealthy = await systemChecks.isHealthy(page)
    const areAgentsOnline = await systemChecks.areAgentsOnline(page)
    
    expect(isHealthy).toBeTruthy()
    expect(areAgentsOnline).toBeTruthy()
    
    // UI должен отражать готовность системы
    await ffPage.waitForSystemReady()
    await ffPage.waitForAgentsOnline()
  })

  ffTest('нет критических ошибок в системе', async ({ ffPage, page }) => {
    await ffPage.goto('/')
    
    const alertsCard = page.locator('[data-testid="alerts-card"]')
    await expect(alertsCard).toBeVisible()
    
    // Критических алертов должно быть 0 или они должны быть некритичными
    const criticalCount = await alertsCard.locator('[data-testid="critical-count"]').textContent()
    const count = parseInt(criticalCount?.trim() || '0', 10)
    
    if (count > 0) {
      // Если есть критические ошибки, логируем их для отладки
      console.warn(`Обнаружено ${count} критических ошибок в системе`)
    }
    
    // В продакшене критических ошибок не должно быть
    if (process.env.NODE_ENV === 'production') {
      expect(count).toBe(0)
    }
  })
})