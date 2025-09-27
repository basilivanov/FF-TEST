import { test, expect } from '@playwright/test'

test.describe('Admin navigation', () => {
  test('navigates main sections', async ({ page }) => {
    await page.goto('/admin')
    await page.waitForLoadState('domcontentloaded')

    // Handle BasicAuth-protected instances gracefully
    const h1 = page.locator('h1')
    const h1Text = (await h1.first().textContent({ timeout: 2000 }).catch(() => null)) || ''
    if (/401 Authorization Required/i.test(h1Text)) {
      test.info().annotations.push({ type: 'skip', description: 'UI behind BasicAuth; credentials not provided in CI env' })
      test.skip(true, 'UI behind BasicAuth')
    }
    // Proceed to direct routes (robust to different shells)

    // Features (direct)
    await page.goto('/admin/features')
    // pick the main heading explicitly
    const mainHeading = page.getByRole('main').getByRole('heading', { name: /Features/i })
    await expect(mainHeading).toBeVisible()

    // Logs (direct)
    await page.goto('/admin/logs')
    await expect(page.getByRole('main').getByRole('heading', { name: /Logs/i })).toBeVisible()

    // Tokens (direct)
    await page.goto('/admin/tokens')
    await expect(page.getByRole('main').getByRole('heading', { name: /Tokens/i })).toBeVisible()

    // Call Graph (direct)
    await page.goto('/admin/call-graph')
    await expect(page.getByRole('heading', { level: 1, name: /System Dependencies/i })).toBeVisible()

    // Docs (direct)
    await page.goto('/admin/docs')
    await expect(page.getByRole('main').getByRole('heading', { name: /Docs/i })).toBeVisible()
  })
})
