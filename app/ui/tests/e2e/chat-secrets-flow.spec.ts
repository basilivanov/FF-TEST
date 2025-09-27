import { test, expect } from '@playwright/test'

test.describe('Product Chat Secret Flow', () => {
  test('REQUEST_SECRETS → fill modal → submit → confirmation in chat', async ({ page }) => {
    // Переходим на страницу чата
    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: /Chat \(Product\)/i })).toBeVisible()

    // Отправляем ввод, который спровоцирует запрос секретов (может зависеть от бэкенд логики)
    const input = page.getByPlaceholder('Введите ваше сообщение...')
    await input.fill('Интеграция с Ozon, нужны ключи')
    await page.getByRole('button', { name: '' }).click() // кнопка отправки (иконка)

    // Ждём появления модалки секретов
    // Подсказка: класс модалки — фиксированный оверлей
    await page.waitForSelector('text=Безопасная отправка секретов', { timeout: 10000 })

    // Вводим тестовые значения (если есть поля)
    const inputs = await page.$$('input[placeholder="Введите значение"]')
    for (const el of inputs) {
      await el.fill('test-secret')
    }

    // Отправка
    const submit = page.getByText('Отправить')
    await submit.click()

    // Ожидаем подтверждающее сообщение в чате
    await expect(page.getByText(/Секрет .* принят и сохранён/i).first()).toBeVisible({ timeout: 10000 })
  })
})

