import { test, expect } from '@playwright/test'

// Для корректной отработки требуется TEST_CHAT_FLOW=1 на backend (чтобы чат мог вернуть подсказку без реального LLM)

test.describe('Product Chat Negative Schema Flow', () => {
  test('Shows hints when schema validation fails (simulated)', async ({ page }) => {
    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: /Chat \(Product\)/i })).toBeVisible()

    // Сообщение, провоцирующее подсказку (симулируем через TEST_CHAT_FLOW)
    const input = page.getByPlaceholder('Введите ваше сообщение...')
    await input.fill('некорректная схема')
    await page.getByTestId('btn-send').click()

    // Ожидаем подсказки о недостающих полях/схеме
    await expect(page.getByText(/Нужно уточнить параметры|Недостаёт/i)).toBeVisible({ timeout: 10000 })
  })
})

