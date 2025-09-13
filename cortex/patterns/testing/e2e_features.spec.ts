// E2E тесты для Features workflow
import { ffTest, expect, setupTestEnvironment } from './e2e_base'

ffTest.describe('Features - Полный жизненный цикл', () => {
  ffTest.beforeEach(async ({ page, correlationId, testUser, baseURL }) => {
    await setupTestEnvironment(page, { correlationId, testUser, baseURL })
  })

  ffTest('создание и обработка новой фичи', async ({ ffPage, page, correlationId }) => {
    const featureTitle = `E2E Test Feature ${correlationId}`
    
    // Создаем фичу
    const featureId = await ffPage.createFeature(featureTitle)
    expect(featureId).toBeTruthy()
    
    // Проверяем, что фича создалась
    const status = await ffPage.getFeatureStatus(featureId)
    expect(['NEW', 'PLANNED', 'RUNNING']).toContain(status)
    
    // Проверяем детали фичи
    await expect(page.locator('[data-testid="feature-title"]')).toContainText(featureTitle)
    await expect(page.locator('[data-testid="feature-status-badge"]')).toBeVisible()
  })

  ffTest('просмотр списка фич с фильтрацией', async ({ ffPage, page }) => {
    await ffPage.goto('/features')
    
    // Проверяем загрузку списка фич
    await expect(page.locator('[data-testid="features-list"]')).toBeVisible()
    
    // Проверяем фильтры статусов
    const statusFilters = page.locator('[data-testid="status-filter"]')
    await expect(statusFilters).toBeVisible()
    
    // Фильтруем по NEW статусу
    await statusFilters.selectOption('NEW')
    await page.waitForLoadState('networkidle')
    
    // Все отображаемые фичи должны иметь статус NEW
    const featureCards = page.locator('[data-testid="feature-card"]')
    const count = await featureCards.count()
    
    for (let i = 0; i < count; i++) {
      const statusBadge = featureCards.nth(i).locator('[data-testid="feature-status"]')
      await expect(statusBadge).toContainText('NEW')
    }
  })

  ffTest('переход между статусами фичи', async ({ ffPage, page, correlationId }) => {
    // Создаем тестовую фичу
    const featureTitle = `Status Transition Test ${correlationId}`
    const featureId = await ffPage.createFeature(featureTitle)
    
    // Изначально статус должен быть NEW или PLANNED
    let status = await ffPage.getFeatureStatus(featureId)
    expect(['NEW', 'PLANNED']).toContain(status)
    
    // Если есть кнопка "Start Processing", нажимаем
    const startButton = page.locator('[data-testid="start-processing-button"]')
    if (await startButton.isVisible()) {
      await startButton.click()
      
      // Ждем изменения статуса
      await page.waitForSelector('[data-testid="feature-status-badge"]:has-text("RUNNING")', {
        timeout: 10000
      })
      
      status = await ffPage.getFeatureStatus(featureId)
      expect(status).toBe('RUNNING')
    }
  })

  ffTest('просмотр прогресса выполнения фичи', async ({ ffPage, page, correlationId }) => {
    // Создаем фичу
    const featureTitle = `Progress Test ${correlationId}`
    const featureId = await ffPage.createFeature(featureTitle)
    
    // Если фича запущена, должен быть виден прогресс
    const status = await ffPage.getFeatureStatus(featureId)
    
    if (status === 'RUNNING') {
      // Проверяем наличие индикатора прогресса
      await expect(page.locator('[data-testid="feature-progress"]')).toBeVisible()
      
      // Проверяем timeline или список задач
      const timeline = page.locator('[data-testid="feature-timeline"]')
      const taskList = page.locator('[data-testid="feature-tasks"]')
      
      const hasProgressIndicator = await timeline.isVisible() || await taskList.isVisible()
      expect(hasProgressIndicator).toBeTruthy()
    }
  })
})

ffTest.describe('Features - Интеграция с API', () => {
  ffTest('API создания фичи работает корректно', async ({ page, correlationId }) => {
    const featureData = {
      title: `API Test Feature ${correlationId}`,
      description: 'Feature created via API for E2E testing',
      priority: 'medium'
    }
    
    // Создаем фичу через API
    const response = await page.request.post('/api/v1/features', {
      data: featureData,
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      }
    })
    
    expect(response.status()).toBe(201)
    const responseData = await response.json()
    
    expect(responseData).toHaveProperty('feature_id')
    expect(responseData.title).toBe(featureData.title)
    
    // Проверяем, что фича отображается в UI
    const featureId = responseData.feature_id
    await page.goto(`/features/${featureId}`)
    
    await expect(page.locator('[data-testid="feature-title"]'))
      .toContainText(featureData.title)
  })

  ffTest('получение статуса фичи через API', async ({ page, ffPage, correlationId }) => {
    // Создаем фичу через UI
    const featureTitle = `API Status Test ${correlationId}`
    const featureId = await ffPage.createFeature(featureTitle)
    
    // Получаем статус через API
    const response = await page.request.get(`/api/v1/features/${featureId}`, {
      headers: { 'X-Correlation-ID': correlationId }
    })
    
    expect(response.status()).toBe(200)
    const data = await response.json()
    
    expect(data).toHaveProperty('id', parseInt(featureId, 10))
    expect(data).toHaveProperty('title', featureTitle)
    expect(data).toHaveProperty('status')
    expect(['NEW', 'PLANNED', 'RUNNING', 'COMPLETED', 'ERROR']).toContain(data.status)
  })
})

ffTest.describe('Features - Обработка ошибок', () => {
  ffTest('обработка ошибок при создании фичи', async ({ page, ffPage }) => {
    await ffPage.goto('/features')
    await page.click('[data-testid="create-feature-button"]')
    
    // Попытка создать фичу без заголовка
    await page.click('[data-testid="submit-feature-button"]')
    
    // Должна появиться ошибка валидации
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible()
    await expect(page.locator('[data-testid="validation-error"]'))
      .toContainText('Title is required')
  })

  ffTest('отображение ошибок выполнения фичи', async ({ page, ffPage, correlationId }) => {
    // Создаем фичу, которая может привести к ошибке
    const featureTitle = `Error Test ${correlationId}`
    const featureId = await ffPage.createFeature(featureTitle)
    
    // Ждем какое-то время для обработки
    await page.waitForTimeout(5000)
    
    const status = await ffPage.getFeatureStatus(featureId)
    
    if (status === 'ERROR') {
      // Проверяем, что ошибка отображается пользователю
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
      
      // Должна быть кнопка для повторной попытки или просмотра логов
      const retryButton = page.locator('[data-testid="retry-button"]')
      const logsButton = page.locator('[data-testid="view-logs-button"]')
      
      const hasRecoveryOption = await retryButton.isVisible() || await logsButton.isVisible()
      expect(hasRecoveryOption).toBeTruthy()
    }
  })
})