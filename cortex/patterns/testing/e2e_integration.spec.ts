// E2E интеграционные тесты для внешних систем
import { ffTest, expect, setupTestEnvironment } from './e2e_base'

ffTest.describe('Integrations - Внешние API', () => {
  ffTest.beforeEach(async ({ page, correlationId, testUser, baseURL }) => {
    await setupTestEnvironment(page, { correlationId, testUser, baseURL })
  })

  ffTest('интеграция с Ozon API', async ({ page, correlationId }) => {
    // Тест интеграции с Ozon (может быть замокан в тестовой среде)
    
    if (process.env.NODE_ENV === 'test') {
      // В тестовой среде мокаем Ozon API
      await page.route('**/api/integrations/ozon/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            data: {
              postings: [
                {
                  posting_id: 'test-123',
                  status: 'delivered',
                  created_at: new Date().toISOString()
                }
              ]
            },
            correlation_id: correlationId
          })
        })
      })
    }
    
    // Тестируем импорт данных через UI или API
    const response = await page.request.post('/api/v1/integrations/ozon/import', {
      data: {
        date_from: '2025-01-01',
        date_to: '2025-01-31'
      },
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      }
    })
    
    expect([200, 201]).toContain(response.status())
    
    const data = await response.json()
    expect(data).toHaveProperty('status')
    expect(data.correlation_id).toBe(correlationId)
  })

  ffTest('проверка обработки ошибок внешних API', async ({ page, correlationId }) => {
    // Мокаем ошибку внешнего API
    await page.route('**/api/integrations/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'External service unavailable',
          correlation_id: correlationId
        })
      })
    })
    
    // Пытаемся сделать запрос к интеграции
    const response = await page.request.post('/api/v1/integrations/test', {
      data: { test: 'data' },
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      }
    })
    
    // Система должна корректно обработать ошибку
    expect(response.status()).toBe(500)
    
    // Ошибка должна быть залогирована
    await page.goto('/logs')
    
    // Ищем ошибку в логах по correlation_id
    const logSearch = page.locator('[data-testid="log-search"]')
    if (await logSearch.isVisible()) {
      await logSearch.fill(correlationId)
      await page.keyboard.press('Enter')
      
      await expect(page.locator('[data-testid="log-entry"]').first())
        .toContainText('External service unavailable')
    }
  })
})

ffTest.describe('Integrations - Маркетплейсы', () => {
  ffTest('подключение и настройка маркетплейса', async ({ page, ffPage, correlationId }) => {
    await ffPage.goto('/integrations')
    
    // Проверяем список доступных интеграций
    await expect(page.locator('[data-testid="integrations-list"]')).toBeVisible()
    
    // Ищем Ozon интеграцию
    const ozonIntegration = page.locator('[data-testid="integration-ozon"]')
    if (await ozonIntegration.isVisible()) {
      // Проверяем статус подключения
      const connectionStatus = ozonIntegration.locator('[data-testid="connection-status"]')
      await expect(connectionStatus).toBeVisible()
      
      const statusText = await connectionStatus.textContent()
      expect(['Connected', 'Disconnected', 'Error']).toContain(statusText?.trim())
      
      // Если не подключено, есть кнопка настройки
      if (statusText?.includes('Disconnected')) {
        const configButton = ozonIntegration.locator('[data-testid="configure-button"]')
        await expect(configButton).toBeVisible()
      }
    }
  })

  ffTest('синхронизация данных с маркетплейсом', async ({ page, correlationId }) => {
    // Запускаем синхронизацию
    const response = await page.request.post('/api/v1/integrations/sync', {
      data: {
        provider: 'ozon',
        sync_type: 'postings'
      },
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      }
    })
    
    if (response.status() === 200) {
      const syncData = await response.json()
      expect(syncData).toHaveProperty('sync_id')
      
      // Проверяем статус синхронизации
      const syncId = syncData.sync_id
      
      // Polling статуса синхронизации
      let attempts = 0
      let syncCompleted = false
      
      while (attempts < 10 && !syncCompleted) {
        await page.waitForTimeout(2000)
        
        const statusResponse = await page.request.get(`/api/v1/integrations/sync/${syncId}`)
        const statusData = await statusResponse.json()
        
        if (statusData.status === 'completed') {
          syncCompleted = true
          expect(statusData.records_processed).toBeGreaterThanOrEqual(0)
        } else if (statusData.status === 'error') {
          console.warn('Sync failed:', statusData.error)
          break
        }
        
        attempts++
      }
    }
  })
})

ffTest.describe('Integrations - AI/ML модели', () => {
  ffTest('интеграция с внешними AI сервисами', async ({ page, correlationId }) => {
    // Тест интеграции с внешними AI API
    
    // Мокаем внешний AI сервис в тестовой среде
    if (process.env.NODE_ENV === 'test') {
      await page.route('**/api/ai/external/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            model: 'test-model-v1',
            response: 'AI generated response for testing',
            tokens_used: 50,
            correlation_id: correlationId
          })
        })
      })
    }
    
    // Отправляем запрос к AI сервису
    const response = await page.request.post('/api/v1/ai/generate', {
      data: {
        prompt: 'Generate test content',
        model: 'external-ai',
        max_tokens: 100
      },
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      }
    })
    
    expect([200, 201]).toContain(response.status())
    
    const aiResponse = await response.json()
    expect(aiResponse).toHaveProperty('response')
    expect(aiResponse).toHaveProperty('tokens_used')
    expect(aiResponse.correlation_id).toBe(correlationId)
  })

  ffTest('мониторинг использования AI моделей', async ({ page, ffPage }) => {
    await ffPage.goto('/ai-models')
    
    // Проверяем список подключенных AI моделей
    await expect(page.locator('[data-testid="ai-models-list"]')).toBeVisible()
    
    // Должна быть статистика использования
    const modelStats = page.locator('[data-testid="model-usage-stats"]')
    if (await modelStats.isVisible()) {
      await expect(modelStats.locator('[data-testid="requests-count"]')).toBeVisible()
      await expect(modelStats.locator('[data-testid="tokens-consumed"]')).toBeVisible()
      await expect(modelStats.locator('[data-testid="cost-estimate"]')).toBeVisible()
    }
  })
})

ffTest.describe('Integrations - Надежность и восстановление', () => {
  ffTest('обработка таймаутов внешних сервисов', async ({ page, correlationId }) => {
    // Мокаем медленный внешний сервис
    await page.route('**/api/integrations/slow/**', route => {
      // Задерживаем ответ на 35 секунд (больше стандартного таймаута)
      setTimeout(() => {
        route.fulfill({
          status: 200,
          body: JSON.stringify({ delayed: true })
        })
      }, 35000)
    })
    
    // Делаем запрос к медленному сервису
    const startTime = Date.now()
    
    const response = await page.request.post('/api/v1/integrations/slow/test', {
      data: { test: 'timeout' },
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      }
    })
    
    const duration = Date.now() - startTime
    
    // Запрос должен завершиться таймаутом быстрее 35 секунд
    expect(duration).toBeLessThan(35000)
    expect([408, 504]).toContain(response.status()) // Request Timeout или Gateway Timeout
  })

  ffTest('retry логика для внешних интеграций', async ({ page, correlationId }) => {
    let attemptCount = 0
    
    // Мокаем сервис, который отвечает успешно только с 3-й попытки
    await page.route('**/api/integrations/retry/**', route => {
      attemptCount++
      
      if (attemptCount < 3) {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: `Attempt ${attemptCount} failed` })
        })
      } else {
        route.fulfill({
          status: 200,
          body: JSON.stringify({ 
            success: true, 
            attempts: attemptCount,
            correlation_id: correlationId 
          })
        })
      }
    })
    
    // Делаем запрос с retry логикой
    const response = await page.request.post('/api/v1/integrations/retry/test', {
      data: { test: 'retry' },
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      }
    })
    
    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.attempts).toBe(3) // Успешно с 3-й попытки
  })

  ffTest('circuit breaker для внешних сервисов', async ({ page, correlationId }) => {
    // Серия неудачных запросов для активации circuit breaker
    const failedRequests = []
    
    // Мокаем постоянно падающий сервис
    await page.route('**/api/integrations/failing/**', route => {
      route.fulfill({
        status: 503,
        body: JSON.stringify({ error: 'Service unavailable' })
      })
    })
    
    // Делаем несколько неудачных запросов
    for (let i = 0; i < 5; i++) {
      const response = await page.request.post('/api/v1/integrations/failing/test', {
        data: { attempt: i + 1 },
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': `${correlationId}-${i}`
        }
      })
      
      failedRequests.push(response.status())
    }
    
    // Все запросы должны были провалиться
    expect(failedRequests.every(status => status >= 500)).toBe(true)
    
    // Следующий запрос должен быть отклонен circuit breaker'ом быстро
    const startTime = Date.now()
    
    const circuitBreakerResponse = await page.request.post('/api/v1/integrations/failing/test', {
      data: { circuit_breaker_test: true },
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': `${correlationId}-circuit-breaker`
      }
    })
    
    const duration = Date.now() - startTime
    
    // Запрос должен завершиться быстро (circuit breaker активен)
    expect(duration).toBeLessThan(1000)
    expect([503, 429]).toContain(circuitBreakerResponse.status())
  })
})