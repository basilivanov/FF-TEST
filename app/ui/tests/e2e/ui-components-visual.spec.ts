import { test, expect } from '@playwright/test'

test.describe('Beautiful UI Components Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin')
    await expect(page.getByRole('heading', { name: /Mission Control Dashboard/i })).toBeVisible()
  })

  test('progress rings should render with correct animations', async ({ page }) => {
    // Проверяем наличие SVG элементов прогресс-колец
    const progressRings = page.locator('svg circle[stroke-dasharray]')
    await expect(progressRings.first()).toBeVisible()
    
    // Проверяем анимацию (transition классы)
    const animatedCircle = page.locator('circle.transition-all')
    if (await animatedCircle.count() > 0) {
      await expect(animatedCircle.first()).toBeVisible()
    }
    
    // Проверяем градиенты в SVG
    const gradientDefs = page.locator('svg defs linearGradient')
    if (await gradientDefs.count() > 0) {
      await expect(gradientDefs.first()).toBeVisible()
    }
  })

  test('sparklines should display with data visualization', async ({ page }) => {
    const sparklineSvg = page.locator('[data-testid="activity-sparkline"] svg')
    await expect(sparklineSvg).toBeVisible()
    
    // Проверяем наличие path элементов для линий
    const sparklinePaths = sparklineSvg.locator('path')
    await expect(sparklinePaths.first()).toBeVisible()
    
    // Проверяем что есть заливка области под линией
    const fillPath = sparklineSvg.locator('path[fill*="gradient"], path[fill*="rgba"]')
    if (await fillPath.count() > 0) {
      await expect(fillPath.first()).toBeVisible()
    }
  })

  test('glass cards should have proper styling effects', async ({ page }) => {
    // Проверяем backdrop-blur эффекты
    const blurredElements = page.locator('.backdrop-blur-md, .backdrop-blur')
    await expect(blurredElements.first()).toBeVisible()
    
    // Проверяем полупрозрачные фоны
    const glassBackgrounds = page.locator('[class*="bg-white/"], [class*="bg-gray-900/"]')
    await expect(glassBackgrounds.first()).toBeVisible()
    
    // Проверяем границы с прозрачностью
    const glassBorders = page.locator('[class*="border-white/"], [class*="border-gray-"]')
    await expect(glassBorders.first()).toBeVisible()
  })

  test('hover effects should work on interactive elements', async ({ page }) => {
    // Тестируем hover эффекты на карточках метрик
    const metricCard = page.locator('[data-testid="llm-agents-metric"]')
    await expect(metricCard).toBeVisible()
    
    // Проверяем что элемент имеет hover классы
    const hoverStyles = await metricCard.getAttribute('class')
    expect(hoverStyles).toContain('cursor-pointer')
    
    // Проверяем hover на кнопках
    const controlButton = page.locator('[data-testid="btn-runner-tick"]')
    await controlButton.hover()
    await expect(controlButton).toBeVisible()
  })

  test('gradient backgrounds and texts should render correctly', async ({ page }) => {
    // Проверяем градиентный фон страницы
    const gradientBg = page.locator('.bg-gradient-to-br')
    await expect(gradientBg.first()).toBeVisible()
    
    // Проверяем градиентный текст заголовка
    const gradientText = page.locator('.bg-gradient-to-r.bg-clip-text.text-transparent')
    await expect(gradientText).toBeVisible()
    
    // Проверяем что текст заголовка читаем
    const title = page.getByRole('heading', { name: /Mission Control Dashboard/i })
    await expect(title).toBeVisible()
  })

  test('status indicators and badges should be colorful and animated', async ({ page }) => {
    // Проверяем цветные статусные индикаторы
    const statusDots = page.locator('.w-2.h-2.rounded-full, .w-3.h-3.rounded-full')
    if (await statusDots.count() > 0) {
      await expect(statusDots.first()).toBeVisible()
    }
    
    // Проверяем бейджи
    const badges = page.locator('[class*="badge"], .bg-yellow-100, .bg-blue-50')
    await expect(badges.first()).toBeVisible()
    
    // Проверяем анимированные элементы
    const animatedElements = page.locator('.animate-pulse, .animate-bounce')
    if (await animatedElements.count() > 0) {
      await expect(animatedElements.first()).toBeVisible()
    }
  })

  test('color scheme should support dark and light modes', async ({ page }) => {
    // Проверяем классы для dark mode
    const darkModeElements = page.locator('[class*="dark:"]')
    await expect(darkModeElements.first()).toBeVisible()
    
    // Проверяем адаптивные цвета
    const adaptiveColors = page.locator('[class*="text-gray-"], [class*="bg-gray-"]')
    await expect(adaptiveColors.first()).toBeVisible()
  })

  test('loading states should display properly', async ({ page }) => {
    // Проверяем кнопку обновления данных
    const refreshButton = page.getByText('Обновить данные')
    await expect(refreshButton).toBeVisible()
    
    // Клик должен показать состояние загрузки
    await refreshButton.click()
    
    // Проверяем иконку loading (может быть animate-spin)
    const spinningIcon = page.locator('.animate-spin')
    if (await spinningIcon.count() > 0) {
      await expect(spinningIcon.first()).toBeVisible()
    }
  })

  test('typography should be consistent and readable', async ({ page }) => {
    // Проверяем различные размеры текста
    const largeText = page.locator('.text-3xl, .text-2xl')
    await expect(largeText.first()).toBeVisible()
    
    const mediumText = page.locator('.text-lg, .text-base')
    await expect(mediumText.first()).toBeVisible()
    
    const smallText = page.locator('.text-sm, .text-xs')
    await expect(smallText.first()).toBeVisible()
    
    // Проверяем жирность шрифта
    const boldText = page.locator('.font-bold, .font-semibold')
    await expect(boldText.first()).toBeVisible()
  })

  test('spacing and layout should be consistent', async ({ page }) => {
    // Проверяем сетку layout
    const gridElements = page.locator('.grid')
    await expect(gridElements.first()).toBeVisible()
    
    // Проверяем промежутки
    const spacedElements = page.locator('[class*="space-y-"], [class*="space-x-"], [class*="gap-"]')
    await expect(spacedElements.first()).toBeVisible()
    
    // Проверяем отступы
    const paddedElements = page.locator('[class*="p-"], [class*="px-"], [class*="py-"]')
    await expect(paddedElements.first()).toBeVisible()
  })

  test('visual hierarchy should be clear', async ({ page }) => {
    // Заголовок должен быть самым заметным
    const mainTitle = page.getByRole('heading', { name: /Mission Control Dashboard/i })
    await expect(mainTitle).toBeVisible()
    
    // Подзаголовки должны быть меньше
    const subtitles = page.locator('h2, h3, .text-lg')
    await expect(subtitles.first()).toBeVisible()
    
    // Карточки должны быть визуально разделены
    const cards = page.locator('[class*="shadow"], [class*="border"], [class*="rounded"]')
    await expect(cards.first()).toBeVisible()
  })

  test('performance metrics visualization should work', async ({ page }) => {
    // Проверяем что метрики отображаются правильно
    const metricsValues = page.locator('.text-3xl.font-bold, .text-2xl.font-bold')
    await expect(metricsValues.first()).toBeVisible()
    
    // Проверяем процентные индикаторы
    const percentages = page.locator(':text-matches("\\d+%")')
    if (await percentages.count() > 0) {
      await expect(percentages.first()).toBeVisible()
    }
    
    // Проверяем числовые метрики
    const numbers = page.locator(':text-matches("\\d+[KM]?")')
    await expect(numbers.first()).toBeVisible()
  })
})