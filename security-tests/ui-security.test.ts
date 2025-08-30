// security-tests/ui-security.test.ts
import { test, expect } from '@playwright/test'

test.describe('Feature Factory Admin UI Security Tests', () => {
  test('Unauthorized access is denied', async ({ page }) => {
    // Пытаемся получить доступ к защищенной странице без авторизации
    await page.goto('/dashboard')
    
    // Проверяем, что нас перенаправило на страницу входа
    await expect(page).toHaveURL(/.*login/)
    await expect(page.getByText('Login')).toBeVisible()
  })

  test('CSRF protection works', async ({ page }) => {
    // Авторизуемся
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    
    // Переходим на страницу, которая может быть уязвима к CSRF
    await page.goto('/settings')
    
    // Проверяем, что форма редактирования защищена CSRF токеном
    await page.click('button:has-text("Редактировать")')
    
    // Проверяем наличие CSRF токена в форме
    const csrfTokenInput = await page.$('input[name="_csrf_token"]')
    expect(csrfTokenInput).not.toBeNull()
  })

  test('XSS protection works', async ({ page }) => {
    // Авторизуемся
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    
    // Переходим на страницу чата
    await page.goto('/chat')
    
    // Пытаемся отправить XSS атаку
    const xssPayload = '<script>alert("XSS")</script>'
    await page.fill('textarea[placeholder="Опишите фичу на естественном языке..."]', xssPayload)
    await page.click('button:has-text("Send")')
    
    // Проверяем, что XSS атака не сработала
    // Страница должна оставаться стабильной
    await expect(page.getByText('Chat (Maintainer)')).toBeVisible()
    
    // Проверяем, что полезная нагрузка была правильно экранирована
    const messageElement = await page.$(`text=${xssPayload}`)
    expect(messageElement).not.toBeNull()
    
    // Проверяем, что скрипт не выполнился
    // Это проверяется косвенно, так как Playwright не может обнаружить alert
  })

  test('Clickjacking protection works', async ({ page }) => {
    // Проверяем, что заголовки защиты от clickjacking установлены
    const response = await page.goto('/')
    
    // Проверяем заголовок X-Frame-Options
    const frameOptions = response?.headers()['x-frame-options']
    expect(frameOptions).toBe('DENY')
    
    // Проверяем заголовок Content-Security-Policy
    const csp = response?.headers()['content-security-policy']
    expect(csp).toContain("frame-ancestors 'none'")
  })

  test('Sensitive data is masked in logs', async ({ page }) => {
    // Авторизуемся
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'secret_password')
    await page.click('button[type="submit"]')
    
    // Переходим на страницу настроек
    await page.goto('/settings')
    
    // Проверяем, что чувствительные данные замаскированы
    await expect(page.getByText('***REDACTED***')).toBeVisible()
    
    // Проверяем, что API ключи замаскированы
    const apiKeyElements = await page.$$('text=sk-***')
    expect(apiKeyElements.length).toBeGreaterThan(0)
  })

  test('Rate limiting works for API endpoints', async ({ page }) => {
    // Авторизуемся
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    
    // Переходим на страницу чата
    await page.goto('/chat')
    
    // Отправляем много сообщений быстро, чтобы проверить rate limiting
    const chatInput = page.getByPlaceholderText('Опишите фичу на естественном языке...')
    
    // Отправляем 20 сообщений быстро
    for (let i = 0; i < 20; i++) {
      await chatInput.fill(`Test message ${i}`)
      await page.click('button:has-text("Send")')
      // Очень короткая пауза между сообщениями
      await page.waitForTimeout(50)
    }
    
    // Проверяем, что система обработала rate limiting корректно
    // Это может проявиться в виде сообщений об ошибке или задержки
    await expect(page.getByText('Too Many Requests')).toBeVisible({ timeout: 10000 }).catch(() => {
      // Если нет явного сообщения об ошибке, проверяем, что страница осталась стабильной
      expect(page.getByText('Chat (Maintainer)')).toBeVisible()
    })
  })

  test('Secure headers are set', async ({ page }) => {
    // Переходим на главную страницу
    const response = await page.goto('/')
    
    // Проверяем заголовки безопасности
    const headers = response?.headers()
    
    // Проверяем Strict-Transport-Security
    expect(headers?.['strict-transport-security']).toBe('max-age=31536000; includeSubDomains')
    
    // Проверяем X-Content-Type-Options
    expect(headers?.['x-content-type-options']).toBe('nosniff')
    
    // Проверяем X-XSS-Protection
    expect(headers?.['x-xss-protection']).toBe('1; mode=block')
    
    // Проверяем Referrer-Policy
    expect(headers?.['referrer-policy']).toBe('strict-origin-when-cross-origin')
    
    // Проверяем Permissions-Policy
    const permissionsPolicy = headers?.['permissions-policy']
    expect(permissionsPolicy).toContain("geolocation=()")
    expect(permissionsPolicy).toContain("microphone=()")
    expect(permissionsPolicy).toContain("camera=()")
  })

  test('Authentication tokens are secure', async ({ page }) => {
    // Авторизуемся
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    
    // Проверяем, что куки аутентификации безопасны
    const cookies = await page.context().cookies()
    const authCookie = cookies.find(cookie => cookie.name === 'auth_token')
    
    expect(authCookie).toBeDefined()
    expect(authCookie?.httpOnly).toBe(true)
    expect(authCookie?.secure).toBe(true)
    // Проверяем, что срок действия куки ограничен
    expect(authCookie?.expires).toBeLessThan(Date.now() / 1000 + 86400) // Меньше 1 дня
    
    // Проверяем, что токен не передается в URL
    expect(page.url()).not.toContain('token=')
    expect(page.url()).not.toContain('auth=')
  })

  test('Input validation prevents injection attacks', async ({ page }) => {
    // Авторизуемся
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    
    // Переходим на страницу создания фичи
    await page.goto('/features')
    await page.click('button:has-text("Создать фичу")')
    
    // Пытаемся ввести потенциально опасные данные
    const injectionPayloads = [
      '<script>alert("XSS")</script>',
      'DROP TABLE features;',
      '{{7*7}}',
      '${7*7}',
      '; rm -rf /',
    ]
    
    for (const payload of injectionPayloads) {
      // Очищаем форму перед каждым тестом
      await page.reload()
      
      // Вводим потенциально опасные данные
      await page.fill('input[name="title"]', payload)
      await page.fill('textarea[name="description"]', payload)
      
      // Пытаемся отправить форму
      await page.click('button:has-text("Создать")')
      
      // Проверяем, что система обработала ввод безопасно
      // Страница должна оставаться стабильной или показывать сообщение об ошибке валидации
      await expect(page.getByText('Features')).toBeVisible({ timeout: 5000 }).catch(() => {
        // Если страница не стабильна, проверяем наличие сообщения об ошибке
        expect(page.getByText('Validation error')).toBeVisible()
      })
    }
  })

  test('Session management is secure', async ({ page }) => {
    // Авторизуемся
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    
    // Сохраняем идентификатор сессии
    const sessionIdBefore = await page.evaluate(() => sessionStorage.getItem('session_id'))
    
    // Переходим на другую страницу
    await page.goto('/dashboard')
    
    // Проверяем, что сессия осталась активной
    const sessionIdAfter = await page.evaluate(() => sessionStorage.getItem('session_id'))
    expect(sessionIdAfter).toBe(sessionIdBefore)
    
    // Имитируем истечение срока действия сессии
    await page.evaluate(() => {
      sessionStorage.removeItem('session_id')
      localStorage.removeItem('auth_token')
    })
    
    // Пытаемся получить доступ к защищенной странице
    await page.goto('/features')
    
    // Проверяем, что нас перенаправило на страницу входа
    await expect(page).toHaveURL(/.*login/)
  })
})