// E2E тесты для Agents (LLM провайдеры)
import { ffTest, expect, setupTestEnvironment } from './e2e_base'

ffTest.describe('Agents - Статус и мониторинг', () => {
  ffTest.beforeEach(async ({ page, correlationId, testUser, baseURL }) => {
    await setupTestEnvironment(page, { correlationId, testUser, baseURL })
  })

  ffTest('отображает статус всех LLM агентов', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    // Проверяем заголовок страницы
    await expect(page.locator('h1')).toContainText('LLM Agents')
    
    // Должна быть таблица с агентами
    await expect(page.locator('[data-testid="agents-table"]')).toBeVisible()
    
    // Проверяем основные колонки
    const headers = page.locator('[data-testid="agents-table"] th')
    await expect(headers).toContainText(['Provider', 'Status', 'Version', 'Path'])
    
    // Должен быть хотя бы один агент
    const agentRows = page.locator('[data-testid="agent-row"]')
    const count = await agentRows.count()
    expect(count).toBeGreaterThan(0)
  })

  ffTest('показывает детальный статус каждого агента', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    // Получаем первый агент из списка
    const firstAgent = page.locator('[data-testid="agent-row"]').first()
    await expect(firstAgent).toBeVisible()
    
    // Проверяем статусные индикаторы
    const statusIndicator = firstAgent.locator('[data-testid="agent-status-indicator"]')
    await expect(statusIndicator).toBeVisible()
    
    // Проверяем информацию о провайдере
    const providerName = firstAgent.locator('[data-testid="agent-provider"]')
    await expect(providerName).toBeVisible()
    
    const providerText = await providerName.textContent()
    expect(['Claude', 'Gemini', 'Qwen', 'Codex']).toContain(providerText?.trim())
  })

  ffTest('проверяет OAuth статус агентов', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    // Ищем агентов с OAuth авторизацией
    const oauthAgents = page.locator('[data-testid="agent-row"]:has([data-testid="oauth-status"])')
    const count = await oauthAgents.count()
    
    if (count > 0) {
      // Проверяем статус OAuth для каждого агента
      for (let i = 0; i < count; i++) {
        const agent = oauthAgents.nth(i)
        const oauthStatus = agent.locator('[data-testid="oauth-status"]')
        
        await expect(oauthStatus).toBeVisible()
        
        const statusText = await oauthStatus.textContent()
        expect(['✅ Logged In', '❌ Not Logged In', '🔄 Refreshing']).toContain(statusText?.trim())
      }
    }
  })

  ffTest('отображает версии и пути агентов', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    const agentRows = page.locator('[data-testid="agent-row"]')
    const count = await agentRows.count()
    
    for (let i = 0; i < count; i++) {
      const agent = agentRows.nth(i)
      
      // Версия должна быть указана
      const version = agent.locator('[data-testid="agent-version"]')
      await expect(version).toBeVisible()
      
      const versionText = await version.textContent()
      expect(versionText?.trim()).toMatch(/^v?\d+\.\d+/)
      
      // Путь должен быть указан
      const path = agent.locator('[data-testid="agent-path"]')
      await expect(path).toBeVisible()
      
      const pathText = await path.textContent()
      expect(pathText?.trim()).toMatch(/^\/.*\/bin\//)
    }
  })
})

ffTest.describe('Agents - Функциональные тесты', () => {
  ffTest('тест связи с агентами через probe команды', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    // Ищем кнопку тестирования агента
    const testButtons = page.locator('[data-testid="test-agent-button"]')
    const count = await testButtons.count()
    
    if (count > 0) {
      const firstTestButton = testButtons.first()
      await firstTestButton.click()
      
      // Должно появиться состояние загрузки
      await expect(firstTestButton).toHaveAttribute('disabled', '')
      
      // Ждем результат теста (успех или ошибка)
      await page.waitForSelector('[data-testid="test-result"]', { timeout: 30000 })
      
      const testResult = page.locator('[data-testid="test-result"]')
      const resultText = await testResult.textContent()
      
      // Результат должен быть либо успешным, либо с описанием ошибки
      expect(resultText).toBeTruthy()
    }
  })

  ffTest('обновление статуса агентов', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    // Кнопка обновления статуса
    const refreshButton = page.locator('[data-testid="refresh-agents-button"]')
    await expect(refreshButton).toBeVisible()
    
    await refreshButton.click()
    
    // Должен появиться индикатор загрузки
    await expect(refreshButton.locator('.animate-spin')).toBeVisible({ timeout: 1000 })
    
    // Ждем завершения обновления
    await expect(refreshButton.locator('.animate-spin')).not.toBeVisible({ timeout: 10000 })
  })

  ffTest('фильтрация агентов по статусу', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    // Проверяем наличие фильтра статуса
    const statusFilter = page.locator('[data-testid="agents-status-filter"]')
    if (await statusFilter.isVisible()) {
      // Фильтруем только онлайн агентов
      await statusFilter.selectOption('online')
      await page.waitForLoadState('networkidle')
      
      // Все отображаемые агенты должны быть онлайн
      const onlineAgents = page.locator('[data-testid="agent-row"]:has([data-testid="status-online"])')
      const totalAgents = page.locator('[data-testid="agent-row"]')
      
      const onlineCount = await onlineAgents.count()
      const totalCount = await totalAgents.count()
      
      expect(onlineCount).toBe(totalCount)
    }
  })
})

ffTest.describe('Agents - Интеграция и надежность', () => {
  ffTest('проверяет работу OAuth refresh токенов', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    // Ищем агентов с истекающими токенами
    const expiredTokenAgents = page.locator('[data-testid="agent-row"]:has([data-testid="token-expired"])')
    const count = await expiredTokenAgents.count()
    
    if (count > 0) {
      // Нажимаем на кнопку обновления токена
      const refreshTokenButton = expiredTokenAgents.first().locator('[data-testid="refresh-token-button"]')
      
      if (await refreshTokenButton.isVisible()) {
        await refreshTokenButton.click()
        
        // Должен запуститься процесс обновления
        await expect(page.locator('[data-testid="token-refreshing"]')).toBeVisible({ timeout: 5000 })
        
        // Ждем завершения обновления
        await expect(page.locator('[data-testid="token-refreshing"]')).not.toBeVisible({ timeout: 60000 })
        
        // Статус должен измениться на "Logged In"
        await expect(expiredTokenAgents.first().locator('[data-testid="oauth-status"]'))
          .toContainText('Logged In', { timeout: 10000 })
      }
    }
  })

  ffTest('проверяет маршрутизацию LLM запросов', async ({ page, ffPage }) => {
    // Эта проверка может требовать реального взаимодействия с LLM
    // В тестовой среде можно замокать или пропустить
    
    if (process.env.NODE_ENV === 'test') {
      ffTest.skip('LLM routing test skipped in test environment')
      return
    }
    
    await ffPage.goto('/agents')
    
    // Проверяем, что есть активные агенты для маршрутизации
    const activeAgents = page.locator('[data-testid="agent-row"]:has([data-testid="status-online"])')
    const activeCount = await activeAgents.count()
    
    expect(activeCount).toBeGreaterThan(0)
    
    // Простой тест маршрутизации через API
    const response = await page.request.post('/api/v1/llm/test', {
      data: {
        message: 'Test routing message',
        role: 'Dev'
      },
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': `e2e-routing-test-${Date.now()}`
      }
    })
    
    // Ответ должен быть успешным
    expect([200, 201]).toContain(response.status())
  })

  ffTest('мониторинг использования бюджета токенов', async ({ page, ffPage }) => {
    await ffPage.goto('/agents')
    
    // Переходим на страницу бюджета
    await page.click('[data-testid="budget-link"]')
    await expect(page).toHaveURL(/\/budget/)
    
    // Проверяем отображение статистики токенов
    await expect(page.locator('[data-testid="token-usage-chart"]')).toBeVisible()
    
    // По каждому провайдеру должна быть статистика
    const providerStats = page.locator('[data-testid="provider-usage"]')
    const statsCount = await providerStats.count()
    
    expect(statsCount).toBeGreaterThan(0)
    
    // У каждого провайдера должны быть метрики
    for (let i = 0; i < statsCount; i++) {
      const stat = providerStats.nth(i)
      await expect(stat.locator('[data-testid="tokens-used"]')).toBeVisible()
      await expect(stat.locator('[data-testid="tokens-limit"]')).toBeVisible()
    }
  })
})