import { test, expect } from '@playwright/test'

test.describe('Admin route sanity', () => {
  test('loads /admin without runtime errors and navigates to logs', async ({ page, baseURL }) => {
    const consoleErrors: string[] = []
    const pageErrors: string[] = []

    page.on('console', (msg) => {
      const type = msg.type()
      if (type === 'error') {
        consoleErrors.push(`[console.${type}] ${msg.text()}`)
      }
    })
    page.on('pageerror', (err) => {
      pageErrors.push(`[pageerror] ${String(err)}`)
    })

    // Go to /admin (Vite dev server will still serve index and our router will pick basename='/admin')
    await page.goto('/admin')
    await page.waitForLoadState('domcontentloaded')

    // If ErrorBoundary shows up, try click "Открыть логи"
    const errTitle = page.locator('text=Произошла ошибка в интерфейсе')
    if (await errTitle.isVisible({ timeout: 2000 }).catch(() => false)) {
      const btn = page.locator('button:has-text("Открыть логи")')
      if (await btn.isVisible()) {
        await btn.click()
        // Should route to /admin/logs (not 404)
        await expect(page).toHaveURL(/\/admin\/logs/)
        // basic sanity element on logs page
        await expect(page.locator('h1')).toBeVisible()
      }
    }

    // Fail if there are hard errors
    const allErrors = [...consoleErrors, ...pageErrors]
    if (allErrors.length) {
      console.log('Collected console errors:', allErrors)
    }
    expect(allErrors.join('\n')).not.toMatch(/TypeError|ReferenceError|is not a function|Uncaught/i)
  })
})

