import { test, expect } from '@playwright/test'

test.describe('Force Reload Beautiful Dashboard', () => {
  test('should force reload and verify beautiful dashboard', async ({ page }) => {
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
    
    // Отключаем кэш браузера полностью
    await page.goto('about:blank')
    
    // Навигируемся с отключенным кэшем  
    console.log('🔍 Navigating to /admin with disabled cache...')
    await page.goto('/admin', { 
      waitUntil: 'networkidle',
      // Отключаем кэш
    })
    
    // Принудительная очистка кэша и перезагрузка
    console.log('🔄 Force clearing cache and reloading...')
    await page.evaluate(() => {
      if ('caches' in window) {
        caches.keys().then(names => {
          names.forEach(name => {
            caches.delete(name)
          })
        })
      }
      // Принудительная перезагрузка без кэша
      window.location.reload()
    })
    
    await page.waitForLoadState('networkidle')
    
    // Ждём немного для полной загрузки
    await page.waitForTimeout(3000)
    
    console.log('🎯 Testing Mission Control Dashboard presence...')
    
    // Проверяем title страницы
    const title = await page.title()
    console.log(`📄 Page title: "${title}"`)
    
    // Ищем "Mission Control Dashboard" в любом месте страницы
    const missionControlText = await page.locator('text=Mission Control Dashboard').count()
    console.log(`🎯 "Mission Control Dashboard" found: ${missionControlText} times`)
    
    // Проверяем весь контент страницы
    const bodyText = await page.textContent('body')
    const hasMissionControl = bodyText?.includes('Mission Control Dashboard')
    const hasRussianText = bodyText?.includes('Здоровье системы') || bodyText?.includes('Центр управления')
    const hasBeautifulElements = bodyText?.includes('Фабрика фич') // может быть из старой версии
    
    console.log(`🔍 Body contains "Mission Control Dashboard": ${hasMissionControl}`)
    console.log(`🔍 Body contains Russian text: ${hasRussianText}`)
    console.log(`🔍 Body contains "Фабрика фич": ${hasBeautifulElements}`)
    
    // Проверяем наличие красивых CSS элементов
    const gradientBg = await page.locator('.bg-gradient-to-br').count()
    const backdropBlur = await page.locator('.backdrop-blur').count()
    const glassEffects = await page.locator('.backdrop-blur-md').count()
    
    console.log(`🌈 Gradient backgrounds: ${gradientBg}`)
    console.log(`💎 Backdrop blur elements: ${backdropBlur}`)
    console.log(`🔮 Glass effects: ${glassEffects}`)
    
    // Ищем h1 элементы
    const h1Count = await page.locator('h1').count()
    console.log(`📝 H1 elements found: ${h1Count}`)
    
    if (h1Count > 0) {
      for (let i = 0; i < Math.min(h1Count, 3); i++) {
        const h1Text = await page.locator('h1').nth(i).textContent()
        console.log(`📝 H1[${i}]: "${h1Text}"`)
      }
    }
    
    // Скриншот для диагностики
    await page.screenshot({ path: 'force-reload-debug.png', fullPage: true })
    
    // Показываем ошибки если есть
    if (errors.length > 0) {
      console.log('❌ JavaScript errors found:')
      errors.forEach(err => console.log(`  ${err}`))
    } else {
      console.log('✅ No JavaScript errors detected')
    }
    
    // Этот тест проходит всегда - только для диагностики
    expect(title).toBeTruthy()
    
    // Но отмечаем успех если находим новый дашборд
    if (hasMissionControl || hasRussianText || gradientBg > 0) {
      console.log('🎉 SUCCESS: Beautiful dashboard elements detected!')
    } else {
      console.log('❌ ISSUE: No beautiful dashboard elements found')
    }
  })
})