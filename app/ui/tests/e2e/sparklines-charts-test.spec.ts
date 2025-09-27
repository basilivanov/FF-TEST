import { test, expect } from '@playwright/test'

test.describe('Sparklines and Charts Dashboard Test', () => {
  test('should show sparklines, progress bars, and charts on dashboard', async ({ page }) => {
    const errors: string[] = []
    
    // Захватываем ошибки
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(`CONSOLE ERROR: ${msg.text()}`)
      }
    })
    
    page.on('pageerror', err => {
      errors.push(`JS ERROR: ${err.message}`)
    })
    
    console.log('🚀 Testing Dashboard with full graphics suite...')
    await page.goto('/admin', { waitUntil: 'networkidle' })
    
    await page.waitForTimeout(3000)
    
    // Проверяем основные элементы дашборда
    const missionControl = await page.locator('text=Mission Control Dashboard').count()
    console.log(`🎯 Mission Control Dashboard: ${missionControl}`)
    expect(missionControl).toBeGreaterThan(0)
    
    // === ТЕСТЫ SPARKLINES ===
    console.log('📈 Testing Sparklines...')
    
    // Ищем sparkline SVG элементы
    const sparklineSvg = await page.locator('svg[data-testid*="sparkline"], svg:has(path[stroke]):not(:has(circle[r="10"]))').count()
    console.log(`📊 Sparkline SVG elements: ${sparklineSvg}`)
    expect(sparklineSvg).toBeGreaterThan(0)
    
    // Проверяем наличие sparkline путей (линии графиков)
    const sparklinePaths = await page.locator('svg path[stroke]:not([fill="none"])').count()
    console.log(`📉 Sparkline paths: ${sparklinePaths}`)
    
    // Проверяем анимированные sparklines
    const animatedSparklines = await page.locator('.animate-pulse').count()
    console.log(`✨ Animated sparkline elements: ${animatedSparklines}`)
    
    // === ТЕСТЫ PROGRESS BARS ===
    console.log('🎗️ Testing Progress Bars...')
    
    // Линейные прогресс-бары
    const progressBars = await page.locator('[data-testid*="progress-bar"], .progress-bar, div[role="progressbar"]').count()
    console.log(`📊 Linear progress bars: ${progressBars}`)
    
    // Прогресс с процентами
    const progressWithPercent = await page.locator('text=/\\d+%/').count()
    console.log(`🔢 Elements with percentages: ${progressWithPercent}`)
    
    // === ТЕСТЫ PROGRESS RINGS ===
    console.log('⭕ Testing Progress Rings...')
    
    // Кольцевые прогресс-индикаторы (SVG circles)
    const progressRings = await page.locator('svg circle[stroke-dasharray]').count()
    console.log(`💍 Progress ring circles: ${progressRings}`)
    expect(progressRings).toBeGreaterThan(0)
    
    // Градиенты в прогресс-рингах
    const progressGradients = await page.locator('svg linearGradient').count()
    console.log(`🌈 Progress gradients: ${progressGradients}`)
    
    // === ТЕСТЫ CHARTS ===  
    console.log('📊 Testing Charts...')
    
    // Радиальные диаграммы здоровья системы
    const systemHealthCharts = await page.locator('[data-testid*="health-chart"], svg:has(circle[r]):has(text)').count()
    console.log(`💚 System health charts: ${systemHealthCharts}`)
    
    // Мини-чарты для агентов
    const agentCharts = await page.locator('[data-testid*="agent-chart"], [data-testid*="llm-chart"]').count()
    console.log(`🤖 Agent status charts: ${agentCharts}`)
    
    // === ТЕСТЫ АНИМАЦИЙ ===
    console.log('🎬 Testing Animations...')
    
    // Элементы с анимациями
    const animatedElements = await page.locator('.animate-pulse, .animate-bounce, .animate-spin').count()
    console.log(`✨ Animated elements: ${animatedElements}`)
    expect(animatedElements).toBeGreaterThan(0)
    
    // CSS transitions
    const transitionElements = await page.locator('[class*="transition"]').count()
    console.log(`🔄 Elements with transitions: ${transitionElements}`)
    
    // === ТЕСТЫ КРАСИВЫХ МЕТРИК ===
    console.log('📋 Testing Beautiful Metrics Cards...')
    
    // Карточки с метриками
    const metricCards = await page.locator('[data-testid*="metric-card"], .metric-card').count()
    console.log(`📋 Metric cards: ${metricCards}`)
    
    // Карточки с числовыми значениями и графикой
    const metricsWithGraphics = await page.locator('.card:has(svg), [class*="card"]:has(svg)').count()
    console.log(`📊 Cards with graphics: ${metricsWithGraphics}`)
    
    // === ФИНАЛЬНАЯ ПРОВЕРКА ===
    
    // Общий счёт всех графических элементов
    const totalGraphics = sparklineSvg + progressRings + animatedElements
    console.log(`🎨 Total graphics elements: ${totalGraphics}`)
    
    // Делаем скриншот
    await page.screenshot({ path: 'sparklines-charts-test.png', fullPage: true })
    
    // Показываем ошибки
    if (errors.length > 0) {
      console.log('❌ JavaScript errors found:')
      errors.forEach(err => console.log(`  ${err}`))
    } else {
      console.log('✅ No JavaScript errors detected')
    }
    
    // ОСНОВНЫЕ ПРОВЕРКИ
    expect(sparklineSvg, 'Should have sparklines').toBeGreaterThan(0)
    expect(progressRings, 'Should have progress rings').toBeGreaterThan(0) 
    expect(animatedElements, 'Should have animations').toBeGreaterThan(0)
    expect(totalGraphics, 'Should have total graphics > 5').toBeGreaterThan(5)
    
    if (totalGraphics > 10) {
      console.log('🎉 EXCELLENT: Rich graphics dashboard confirmed!')
    } else if (totalGraphics > 5) {
      console.log('✅ GOOD: Basic graphics present')
    } else {
      console.log('❌ NEEDS IMPROVEMENT: Not enough graphics')
    }
  })
})