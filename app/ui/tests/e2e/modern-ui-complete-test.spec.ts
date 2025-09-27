import { test, expect } from '@playwright/test'

test.describe('Complete Modern UI Test - Sparklines, Charts, Tooltips, Hovers', () => {
  test('should have full modern UI with sparklines, progress bars, tooltips, and hover effects', async ({ page }) => {
    const errors: string[] = []
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(`CONSOLE ERROR: ${msg.text()}`)
      }
    })
    
    page.on('pageerror', err => {
      errors.push(`JS ERROR: ${err.message}`)
    })
    
    console.log('🚀 Testing Complete Modern UI Suite...')
    await page.goto('/admin', { waitUntil: 'networkidle' })
    await page.waitForTimeout(5000)
    
    // === БАЗОВЫЕ ЭЛЕМЕНТЫ ===
    const missionControl = await page.locator('text=Mission Control Dashboard').count()
    console.log(`🎯 Mission Control Dashboard: ${missionControl}`)
    expect(missionControl).toBeGreaterThan(0)
    
    // === 1. SPARKLINES 📈 ===
    console.log('\\n📈 Testing Sparklines...')
    
    const sparklineSvgs = await page.locator('[data-testid*="sparkline"], .sparkline, svg:has(path[stroke-width="2"])').count()
    console.log(`📊 Sparkline elements: ${sparklineSvgs}`)
    
    const sparklinePaths = await page.locator('svg path[stroke]:not([fill])').count()
    console.log(`📉 Sparkline paths: ${sparklinePaths}`)
    
    const animatedSparklines = await page.locator('svg path[style*="animation"], svg path[class*="animate"]').count()
    console.log(`✨ Animated sparklines: ${animatedSparklines}`)
    
    // === 2. PROGRESS BARS & RINGS 🎗️ ===
    console.log('\\n🎗️ Testing Progress Elements...')
    
    // Линейные прогресс-бары
    const linearProgress = await page.locator('[data-testid*="progress-bar"], .progress-bar, div[role="progressbar"]').count()
    console.log(`📊 Linear progress bars: ${linearProgress}`)
    
    // Кольцевые прогресс-индикаторы
    const progressRings = await page.locator('[data-testid*="progress-ring"], svg circle[stroke-dasharray]').count()
    console.log(`💍 Progress rings: ${progressRings}`)
    
    // Процентные значения
    const percentageLabels = await page.locator('text=/\\d+%/', '[data-testid*="percentage"]').count()
    console.log(`🔢 Percentage labels: ${percentageLabels}`)
    
    // === 3. CHARTS & GRAPHS 📊 ===
    console.log('\\n📊 Testing Charts...')
    
    // Радиальные диаграммы
    const radialCharts = await page.locator('[data-testid*="radial-chart"], [data-testid*="health-chart"]').count()
    console.log(`🎯 Radial charts: ${radialCharts}`)
    
    // Мини-чарты для метрик
    const miniCharts = await page.locator('[data-testid*="mini-chart"], .mini-chart').count()
    console.log(`📈 Mini charts: ${miniCharts}`)
    
    // SVG графические элементы
    const svgElements = await page.locator('svg').count()
    console.log(`🎨 Total SVG elements: ${svgElements}`)
    
    // === 4. TOOLTIPS & ПОДСКАЗКИ 💬 ===
    console.log('\\n💬 Testing Tooltips...')
    
    // Элементы с title (нативные тултипы)
    const titleTooltips = await page.locator('[title]').count()
    console.log(`📝 Elements with title tooltips: ${titleTooltips}`)
    
    // Кастомные тултипы
    const customTooltips = await page.locator('[data-testid*="tooltip"], .tooltip').count()
    console.log(`🎈 Custom tooltip elements: ${customTooltips}`)
    
    // Тестируем ховер для тултипов (на первом элементе с title)
    if (titleTooltips > 0) {
      const firstTooltipElement = await page.locator('[title]').first()
      await firstTooltipElement.hover()
      await page.waitForTimeout(1000)
      console.log(`🖱️ Hovered over tooltip element`)
    }
    
    // === 5. HOVER EFFECTS 🖱️ ===
    console.log('\\n🖱️ Testing Hover Effects...')
    
    // Элементы с hover классами
    const hoverElements = await page.locator('[class*="hover:"]').count()
    console.log(`✨ Elements with hover effects: ${hoverElements}`)
    
    // Кнопки и интерактивные элементы
    const interactiveElements = await page.locator('button, [role="button"], .cursor-pointer').count()
    console.log(`🖱️ Interactive elements: ${interactiveElements}`)
    
    // Тестируем ховер на кнопках
    const buttons = await page.locator('button').all()
    if (buttons.length > 0) {
      for (let i = 0; i < Math.min(buttons.length, 3); i++) {
        await buttons[i].hover()
        await page.waitForTimeout(500)
        console.log(`🖱️ Hovered over button ${i + 1}`)
      }
    }
    
    // === 6. АНИМАЦИИ & TRANSITIONS ✨ ===
    console.log('\\n✨ Testing Animations...')
    
    const animatedElements = await page.locator('.animate-pulse, .animate-bounce, .animate-spin, .animate-ping').count()
    console.log(`🎬 CSS animated elements: ${animatedElements}`)
    
    const transitionElements = await page.locator('[class*="transition"], [class*="duration"]').count()
    console.log(`🔄 Elements with transitions: ${transitionElements}`)
    
    // === 7. LOADING STATES 🔄 ===
    console.log('\\n🔄 Testing Loading States...')
    
    const loadingSpinners = await page.locator('.animate-spin, [data-testid*="loading"], .loading').count()
    console.log(`🌀 Loading spinners: ${loadingSpinners}`)
    
    const skeletonLoaders = await page.locator('[class*="skeleton"], [data-testid*="skeleton"]').count()
    console.log(`💀 Skeleton loaders: ${skeletonLoaders}`)
    
    // === 8. STATUS INDICATORS 🚦 ===
    console.log('\\n🚦 Testing Status Indicators...')
    
    const statusBadges = await page.locator('.badge, [data-testid*="status"], [class*="badge"]').count()
    console.log(`🏷️ Status badges: ${statusBadges}`)
    
    const healthIndicators = await page.locator('text=/🟢|🔴|🟡|✅|❌|⚠️/').count()
    console.log(`💚 Health indicators: ${healthIndicators}`)
    
    // === 9. ГРАДИЕНТЫ & ЭФФЕКТЫ 🌈 ===
    console.log('\\n🌈 Testing Visual Effects...')
    
    const gradientElements = await page.locator('[class*="gradient"], svg linearGradient').count()
    console.log(`🌈 Gradient elements: ${gradientElements}`)
    
    const glassEffects = await page.locator('[class*="backdrop-blur"], .glass-effect').count()
    console.log(`💎 Glass effects: ${glassEffects}`)
    
    const shadowElements = await page.locator('[class*="shadow"]').count()
    console.log(`🌑 Shadow effects: ${shadowElements}`)
    
    // === ФИНАЛЬНАЯ ОЦЕНКА ===
    const totalGraphics = sparklineSvgs + progressRings + radialCharts + svgElements
    const totalInteractivity = hoverElements + customTooltips + interactiveElements
    const totalAnimations = animatedElements + transitionElements + loadingSpinners
    const totalEffects = gradientElements + glassEffects + shadowElements
    
    const totalScore = totalGraphics + totalInteractivity + totalAnimations + totalEffects
    
    console.log('\\n🎯 === FINAL SCORE ===')
    console.log(`📊 Graphics elements: ${totalGraphics}`)
    console.log(`🖱️ Interactive elements: ${totalInteractivity}`) 
    console.log(`✨ Animations: ${totalAnimations}`)
    console.log(`🎨 Visual effects: ${totalEffects}`)
    console.log(`🏆 TOTAL MODERN UI SCORE: ${totalScore}`)
    
    // Делаем скриншот
    await page.screenshot({ path: 'modern-ui-complete-test.png', fullPage: true })
    
    // Логируем ошибки
    if (errors.length > 0) {
      console.log('\\n❌ JavaScript errors:')
      errors.forEach(err => console.log(`  ${err}`))
    } else {
      console.log('\\n✅ No JavaScript errors')
    }
    
    // === ТРЕБОВАНИЯ К ТЕСТУ ===
    expect(sparklineSvgs, 'Should have sparklines').toBeGreaterThan(0)
    expect(progressRings, 'Should have progress rings').toBeGreaterThan(0)
    expect(hoverElements, 'Should have hover effects').toBeGreaterThan(0)  
    expect(totalScore, 'Total modern UI score should be > 20').toBeGreaterThan(20)
    
    if (totalScore > 50) {
      console.log('🎉 OUTSTANDING: World-class modern UI!')
    } else if (totalScore > 30) {
      console.log('✅ EXCELLENT: Great modern UI implementation')
    } else if (totalScore > 20) {
      console.log('👍 GOOD: Solid modern UI elements')  
    } else {
      console.log('❌ NEEDS WORK: More modern UI elements required')
    }
  })
})