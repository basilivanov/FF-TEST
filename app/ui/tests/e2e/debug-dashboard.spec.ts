import { test, expect } from '@playwright/test'

test.describe('Debug Dashboard Loading', () => {
  test('should load dashboard and show console errors', async ({ page }) => {
    const errors: string[] = []
    
    // Захватываем console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(`CONSOLE ERROR: ${msg.text()}`)
      }
    })
    
    // Захватываем JS errors
    page.on('pageerror', err => {
      errors.push(`JS ERROR: ${err.message}`)
    })
    
    console.log('🔍 Navigating to /admin...')
    await page.goto('/admin', { waitUntil: 'networkidle' })
    
    // Принудительно перезагружаем без кэша
    console.log('🔄 Hard refresh without cache...')
    await page.reload({ waitUntil: 'networkidle' })
    
    // Ждём немного чтобы JS успел загрузиться
    await page.waitForTimeout(3000)
    
    // Проверяем что хотя бы страница загрузилась
    const title = await page.title()
    console.log(`📄 Page title: ${title}`)
    
    // Ищем любой h1 на странице
    const h1Elements = await page.locator('h1').count()
    console.log(`📝 Found ${h1Elements} h1 elements`)
    
    if (h1Elements > 0) {
      const h1Text = await page.locator('h1').first().textContent()
      console.log(`📝 First h1 text: "${h1Text}"`)
    }
    
    // Проверяем специфично на "Mission Control Dashboard"
    const missionControlExists = await page.locator(':has-text("Mission Control Dashboard")').count()
    console.log(`🎯 Mission Control Dashboard elements: ${missionControlExists}`)
    
    // Проверяем на наши красивые компоненты
    const glassCardExists = await page.locator('.backdrop-blur').count()
    console.log(`🎨 Glass effect elements: ${glassCardExists}`)
    
    const gradientBgExists = await page.locator('.bg-gradient-to-br').count()
    console.log(`🌈 Gradient background elements: ${gradientBgExists}`)
    
    // Ищем тестовые ID наших компонентов
    const systemHealthWidget = await page.locator('[data-testid="system-health-widget"]').count()
    console.log(`💚 System health widget: ${systemHealthWidget}`)
    
    const llmAgentsMetric = await page.locator('[data-testid="llm-agents-metric"]').count()
    console.log(`🤖 LLM agents metric: ${llmAgentsMetric}`)
    
    // Ищем элементы с роль heading
    const headingElements = await page.locator('[role="heading"], h1, h2, h3').count()
    console.log(`📝 Found ${headingElements} heading elements`)
    
    // Проверяем весь текстовый контент страницы
    const bodyText = await page.locator('body').textContent()
    const hasMissionControl = bodyText?.includes('Mission Control Dashboard')
    const hasBeautifulElements = bodyText?.includes('Здоровье системы')
    console.log(`🔍 Page contains "Mission Control Dashboard": ${hasMissionControl}`)
    console.log(`🔍 Page contains "Здоровье системы": ${hasBeautifulElements}`)
    
    // Показываем все ошибки
    if (errors.length > 0) {
      console.log('❌ Errors found:')
      errors.forEach(err => console.log(`  ${err}`))
    } else {
      console.log('✅ No console/JS errors detected')
    }
    
    // Делаем скриншот для диагностики
    await page.screenshot({ path: 'dashboard-debug.png', fullPage: true })
    
    // Этот тест всегда проходит - он только для диагностики
    expect(title).toBeTruthy()
  })
})