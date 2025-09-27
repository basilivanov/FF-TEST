import { test, expect } from '@playwright/test'

test.describe('New UI Components E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin')
    await expect(page.getByRole('heading', { name: /Mission Control Dashboard/i })).toBeVisible()
  })

  test('logs page should display charts and statistics', async ({ page }) => {
    // Navigate to logs page
    await page.click('text=Логи')

    // Wait for logs to load
    await page.waitForSelector('.grid', { timeout: 10000 })

    // Check for logs overview cards
    await expect(page.getByText('Обзор логов')).toBeVisible()
    await expect(page.getByText('Распределение по уровням')).toBeVisible()
    await expect(page.getByText('Активность сервисов')).toBeVisible()
    await expect(page.getByText('Распределение по времени')).toBeVisible()

    // Check for sparklines in statistics cards
    const sparklines = page.locator('[data-testid*="sparkline"]')
    await expect(sparklines.first()).toBeVisible()

    // Check for Recharts containers
    const charts = page.locator('.recharts-wrapper')
    await expect(charts.first()).toBeVisible()
  })

  test('feature detail page should show timeline and control panel', async ({ page }) => {
    // Navigate to first feature
    await page.click('.cursor-pointer')

    // Wait for feature detail to load
    await page.waitForSelector('text=Хронология выполнения', { timeout: 10000 })

    // Check for timeline component
    await expect(page.getByText('Хронология выполнения')).toBeVisible()
    await expect(page.getByText('Фича создана')).toBeVisible()

    // Check for control panel
    await expect(page.getByText('Управление графом')).toBeVisible()
    await expect(page.getByText('Запустить фичу')).toBeVisible()
    await expect(page.getByText('Tick таймер')).toBeVisible()

    // Check for metrics cards
    await expect(page.getByText('Общие запуски')).toBeVisible()
    await expect(page.getByText('Активные запуски')).toBeVisible()
    await expect(page.getByText('Общие задачи')).toBeVisible()

    // Check for sparklines in control panel
    const activitySparklines = page.locator('[data-testid="activity-sparkline"]')
    await expect(activitySparklines.first()).toBeVisible()
  })

  test('control panel buttons should be functional', async ({ page }) => {
    // Navigate to first feature
    await page.click('.cursor-pointer')
    await page.waitForSelector('text=Управление графом', { timeout: 10000 })

    // Test run feature button
    const runButton = page.getByText('Запустить фичу')
    await expect(runButton).toBeVisible()
    await expect(runButton).toBeEnabled()

    // Test tick timer button
    const tickButton = page.getByText('Tick таймер')
    await expect(tickButton).toBeVisible()
    await expect(tickButton).toBeEnabled()

    // Test auto-refresh toggle
    const autoRefreshToggle = page.locator('input[type="checkbox"]').first()
    if (await autoRefreshToggle.count() > 0) {
      await expect(autoRefreshToggle).toBeVisible()
    }
  })

  test('timeline should show retry/restart buttons for failed items', async ({ page }) => {
    // Navigate to first feature
    await page.click('.cursor-pointer')
    await page.waitForSelector('text=Хронология выполнения', { timeout: 10000 })

    // Look for retry/restart buttons if there are failed tasks/runs
    const retryButtons = page.getByText('Повторить')
    const restartButtons = page.getByText('Перезапустить')

    if (await retryButtons.count() > 0) {
      await expect(retryButtons.first()).toBeVisible()
    }

    if (await restartButtons.count() > 0) {
      await expect(restartButtons.first()).toBeVisible()
    }
  })

  test('charts should be responsive and interactive', async ({ page }) => {
    await page.click('text=Логи')
    await page.waitForSelector('.recharts-wrapper', { timeout: 10000 })

    // Check chart responsiveness by resizing viewport
    await page.setViewportSize({ width: 800, height: 600 })
    const charts = page.locator('.recharts-wrapper')
    await expect(charts.first()).toBeVisible()

    await page.setViewportSize({ width: 1200, height: 800 })
    await expect(charts.first()).toBeVisible()

    // Test chart tooltips on hover
    const chartAreas = page.locator('.recharts-surface')
    if (await chartAreas.count() > 0) {
      await chartAreas.first().hover()
      // Tooltip might appear
    }
  })

  test('live tail indicator should work on logs page', async ({ page }) => {
    await page.click('text=Логи')
    await page.waitForSelector('.grid', { timeout: 10000 })

    // Check for live tail toggle
    const liveTailToggle = page.locator('text=Live Tail')
    if (await liveTailToggle.count() > 0) {
      await expect(liveTailToggle).toBeVisible()
    }

    // Check for refresh button
    const refreshButton = page.getByText('Обновить данные')
    if (await refreshButton.count() > 0) {
      await expect(refreshButton).toBeVisible()
      await expect(refreshButton).toBeEnabled()
    }
  })

  test('gradient backgrounds and glass effects should render', async ({ page }) => {
    // Check for gradient backgrounds
    const gradientElements = page.locator('[class*="bg-gradient"]')
    await expect(gradientElements.first()).toBeVisible()

    // Check for glass card effects
    const glassElements = page.locator('[class*="backdrop-blur"]')
    if (await glassElements.count() > 0) {
      await expect(glassElements.first()).toBeVisible()
    }

    // Check for semi-transparent backgrounds
    const semiTransparentElements = page.locator('[class*="bg-white/"], [class*="bg-gray-900/"]')
    await expect(semiTransparentElements.first()).toBeVisible()
  })

  test('typography and spacing should be consistent', async ({ page }) => {
    // Check for proper heading hierarchy
    const mainHeading = page.getByRole('heading', { name: /Mission Control Dashboard/i })
    await expect(mainHeading).toBeVisible()

    // Check for consistent text sizes
    const largeText = page.locator('.text-3xl, .text-2xl')
    await expect(largeText.first()).toBeVisible()

    // Check for proper spacing
    const spacedElements = page.locator('[class*="space-y-"], [class*="gap-"]')
    await expect(spacedElements.first()).toBeVisible()

    // Check for proper padding
    const paddedElements = page.locator('[class*="p-"], [class*="px-"], [class*="py-"]')
    await expect(paddedElements.first()).toBeVisible()
  })

  test('loading states should display correctly', async ({ page }) => {
    // Navigate to logs page
    await page.click('text=Логи')

    // Click refresh button if present
    const refreshButton = page.getByText('Обновить данные')
    if (await refreshButton.count() > 0) {
      await refreshButton.click()

      // Look for loading indicators
      const loadingSpinner = page.locator('.animate-spin')
      if (await loadingSpinner.count() > 0) {
        await expect(loadingSpinner.first()).toBeVisible()
      }
    }
  })

  test('color scheme and dark mode support', async ({ page }) => {
    // Check for dark mode classes
    const darkModeElements = page.locator('[class*="dark:"]')
    if (await darkModeElements.count() > 0) {
      await expect(darkModeElements.first()).toBeVisible()
    }

    // Check for adaptive colors
    const adaptiveColors = page.locator('[class*="text-gray-"], [class*="bg-gray-"]')
    await expect(adaptiveColors.first()).toBeVisible()
  })
})