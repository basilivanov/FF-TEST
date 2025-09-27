import { test, expect } from '@playwright/test'

test.describe('Beautiful Dashboard Components', () => {
  test.beforeEach(async ({ page }) => {
    // Переходим на дашборд
    await page.goto('/admin')
    
    // Ждём загрузки основных элементов
    await expect(page.getByRole('heading', { name: /Mission Control Dashboard/i })).toBeVisible()
  })

  test('should display system health radial chart', async ({ page }) => {
    // Проверяем наличие виджета здоровья системы
    const healthWidget = page.locator('[data-testid="system-health-widget"]')
    await expect(healthWidget).toBeVisible()
    
    // Проверяем радиальную диаграмму общего здоровья
    const overallHealthRing = page.locator('[data-testid="overall-health-ring"]')
    await expect(overallHealthRing).toBeVisible()
    
    // Проверяем мини-кольца для отдельных метрик (должно быть 4)
    const metricRings = page.locator('[data-testid^="metric-ring-"]')
    await expect(metricRings).toHaveCount(4)
    
    // Проверяем легенду статусов
    await expect(page.getByText('Здорово')).toBeVisible()
    await expect(page.getByText('Предупреждение')).toBeVisible()
    await expect(page.getByText('Критично')).toBeVisible()
  })

  test('should display metric cards with progress rings and sparklines', async ({ page }) => {
    // Проверяем карточку LLM Агентов
    const agentsMetric = page.locator('[data-testid="llm-agents-metric"]')
    await expect(agentsMetric).toBeVisible()
    await expect(agentsMetric.getByText('LLM Агенты')).toBeVisible()
    await expect(agentsMetric.getByText('Активных агентов')).toBeVisible()
    
    // Проверяем карточку активных процессов
    const processesMetric = page.locator('[data-testid="active-processes-metric"]')
    await expect(processesMetric).toBeVisible()
    await expect(processesMetric.getByText('Активные процессы')).toBeVisible()
    await expect(processesMetric.getByText('Запуски + Фичи')).toBeVisible()
    
    // Проверяем карточку бюджета токенов
    const budgetMetric = page.locator('[data-testid="token-budget-metric"]')
    await expect(budgetMetric).toBeVisible()
    await expect(budgetMetric.getByText('Бюджет токенов')).toBeVisible()
    
    // Проверяем карточку критических событий
    const eventsMetric = page.locator('[data-testid="critical-events-metric"]')
    await expect(eventsMetric).toBeVisible()
    await expect(eventsMetric.getByText('Критические события')).toBeVisible()
    await expect(eventsMetric.getByText('За последний час')).toBeVisible()
  })

  test('should display activity sparkline in backlog section', async ({ page }) => {
    // Проверяем спарклайн активности
    const activitySparkline = page.locator('[data-testid="activity-sparkline"]')
    await expect(activitySparkline).toBeVisible()
    
    // Проверяем текст рядом со спарклайном
    await expect(page.getByText('Активность за день')).toBeVisible()
    
    // Проверяем наличие иконки тренда
    const trendIcon = page.locator('svg').filter({ hasText: /trending-up/i })
    await expect(trendIcon.first()).toBeVisible()
  })

  test('should have glassmorphism and gradient effects', async ({ page }) => {
    // Проверяем, что карточки имеют стили стекла (backdrop-blur)
    const glassCards = page.locator('.backdrop-blur-md, .backdrop-blur')
    await expect(glassCards.first()).toBeVisible()
    
    // Проверяем наличие градиентного фона
    const gradientBg = page.locator('.bg-gradient-to-br')
    await expect(gradientBg.first()).toBeVisible()
    
    // Проверяем градиентный текст заголовка
    const gradientText = page.locator('.bg-gradient-to-r.from-blue-600.to-purple-600')
    await expect(gradientText).toBeVisible()
  })

  test('should have animated elements', async ({ page }) => {
    // Проверяем пульсирующие элементы
    const pulsingElements = page.locator('.animate-pulse')
    await expect(pulsingElements.first()).toBeVisible()
    
    // Проверяем наличие анимированных иконок
    const activityIcon = page.locator('svg[class*="animate-pulse"]').first()
    await expect(activityIcon).toBeVisible()
    
    // Проверяем индикаторы статуса с анимацией
    const statusIndicators = page.locator('.w-2.h-2.rounded-full.animate-pulse')
    if (await statusIndicators.count() > 0) {
      await expect(statusIndicators.first()).toBeVisible()
    }
  })

  test('should maintain functionality of control buttons', async ({ page }) => {
    // Проверяем кнопку "Ускорить раннер"
    const runnerButton = page.locator('[data-testid="btn-runner-tick"]')
    await expect(runnerButton).toBeVisible()
    await expect(runnerButton.getByText('Ускорить раннер')).toBeVisible()
    
    // Проверяем кнопку "Обновить агентов"
    const agentsButton = page.locator('[data-testid="btn-agents-refresh"]')
    await expect(agentsButton).toBeVisible()
    await expect(agentsButton.getByText('Обновить агентов')).toBeVisible()
    
    // Проверяем кнопку обновления данных
    const refreshButton = page.getByText('Обновить данные')
    await expect(refreshButton).toBeVisible()
    
    // Проверяем кнопку журнала событий
    const logsButton = page.getByText('Журнал событий')
    await expect(logsButton).toBeVisible()
  })

  test('should navigate properly when clicking on metric cards', async ({ page }) => {
    // Клик на карточку агентов должен перевести на страницу агентов
    const agentsMetric = page.locator('[data-testid="llm-agents-metric"]')
    await agentsMetric.click()
    await expect(page).toHaveURL(/.*\/agents$/)
    
    // Возвращаемся на дашборд
    await page.goto('/admin')
    
    // Клик на карточку активных процессов должен перевести на страницу фич
    const processesMetric = page.locator('[data-testid="active-processes-metric"]')
    await processesMetric.click()
    await expect(page).toHaveURL(/.*\/features$/)
    
    // Возвращаемся на дашборд
    await page.goto('/admin')
    
    // Клик на карточку токенов должен перевести на страницу токенов
    const budgetMetric = page.locator('[data-testid="token-budget-metric"]')
    await budgetMetric.click()
    await expect(page).toHaveURL(/.*\/tokens$/)
  })

  test('should be responsive and look good on different screen sizes', async ({ page }) => {
    // Проверяем на большом экране
    await page.setViewportSize({ width: 1920, height: 1080 })
    await expect(page.getByRole('heading', { name: /Mission Control Dashboard/i })).toBeVisible()
    
    // Проверяем на планшете
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page.getByRole('heading', { name: /Mission Control Dashboard/i })).toBeVisible()
    
    // Проверяем на мобильном
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.getByRole('heading', { name: /Mission Control Dashboard/i })).toBeVisible()
    
    // Убеждаемся что элементы не обрезаются
    const mainContent = page.locator('main')
    await expect(mainContent).toBeVisible()
  })

  test('should display proper Russian text throughout the interface', async ({ page }) => {
    // Проверяем основные русские заголовки и тексты
    await expect(page.getByText('Здоровье системы')).toBeVisible()
    await expect(page.getByText('Активных агентов')).toBeVisible()
    await expect(page.getByText('Бэклог и очередь')).toBeVisible()
    await expect(page.getByText('Активные процессы')).toBeVisible()
    await expect(page.getByText('Центр управления фабрикой фич')).toBeVisible()
    await expect(page.getByText('мониторинг, управление и аналитика в реальном времени')).toBeVisible()
    
    // Проверяем кнопки с русским текстом
    await expect(page.getByText('Открыть все фичи')).toBeVisible()
    await expect(page.getByText('Ускорить раннер')).toBeVisible()
    await expect(page.getByText('Обновить агентов')).toBeVisible()
    await expect(page.getByText('Журнал событий')).toBeVisible()
    await expect(page.getByText('Обновить данные')).toBeVisible()
  })
})