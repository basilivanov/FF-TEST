import { test, expect } from '@playwright/test'

// ВНИМАНИЕ: требуется запущенный backend с TEST_CHAT_FLOW=1, чтобы чат отвечал детерминированно

test.describe('Product Chat Finalization Flow', () => {
  test('From secrets to finalize (TEST_CHAT_FLOW)', async ({ page }) => {
    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: /Chat \(Product\)/i })).toBeVisible()

    // Шаг 1: запрос, который приведёт к REQUEST_SECRETS (в тестовом режиме)
    const input = page.getByPlaceholder('Введите ваше сообщение...')
    await input.fill('Интеграция с Ozon — нужны секреты')
    await page.getByTestId('btn-send').click()

    // Модалка секретов
    await page.waitForSelector('[data-testid="secret-modal"]', { timeout: 10000 })
    const secretInputs = await page.$$('input[placeholder="Введите значение"]')
    for (const el of secretInputs) {
      await el.fill('test-secret')
    }
    await page.getByTestId('secret-submit').click()

    // Должно появиться подтверждающее сообщение
    await expect(page.getByText(/Секрет .* принят и сохранён/i).first()).toBeVisible({ timeout: 10000 })

    // Ждём бейдж готовности ≥ 0.85 и просим финализацию
    await expect(page.getByText(/Готовность: 0\.(8|9)\d/i)).toBeVisible({ timeout: 10000 })
    const finalizeBtn = page.getByTestId('btn-request-finalize')
    await expect(finalizeBtn).toBeVisible()
    await finalizeBtn.click()

  // Ожидаем подтверждение финализации в чате
  await expect(page.getByText(/Ваша задача успешно зарегистрирована/i)).toBeVisible({ timeout: 10000 })
  // Ожидаем тост с ссылкой
  const toast = page.getByTestId('toast-feature-created')
  await expect(toast).toBeVisible()
  const link = toast.getByRole('link', { name: /Перейти/i })
  await expect(link).toHaveAttribute('href', /\/features\//)
  })
})
