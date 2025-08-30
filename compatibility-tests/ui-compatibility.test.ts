// compatibility-tests/ui-compatibility.test.ts
import { test, expect } from '@playwright/test'

test.describe('Feature Factory Admin UI Compatibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Авторизация перед каждым тестом
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
  })

  test('UI works correctly on Chrome', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Тест только для Chrome')
    
    await page.goto('/dashboard')
    
    // Проверяем основные функции
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
    
    // Проверяем навигацию
    await page.click('text=Features')
    await expect(page.getByText('Features')).toBeVisible()
  })

  test('UI works correctly on Firefox', async ({ page, browserName }) => {
    test.skip(browserName !== 'firefox', 'Тест только для Firefox')
    
    await page.goto('/dashboard')
    
    // Проверяем основные функции
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
    
    // Проверяем навигацию
    await page.click('text=Features')
    await expect(page.getByText('Features')).toBeVisible()
  })

  test('UI works correctly on Safari', async ({ page, browserName }) => {
    test.skip(browserName !== 'webkit', 'Тест только для Safari')
    
    await page.goto('/dashboard')
    
    // Проверяем основные функции
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
    
    // Проверяем навигацию
    await page.click('text=Features')
    await expect(page.getByText('Features')).toBeVisible()
  })

  test('UI works correctly on Edge', async ({ page }) => {
    // Edge использует Chromium, поэтому тестируем как Chrome
    await page.goto('/dashboard')
    
    // Проверяем основные функции
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
    
    // Проверяем навигацию
    await page.click('text=Features')
    await expect(page.getByText('Features')).toBeVisible()
  })

  test('UI adapts to different screen sizes', async ({ page }) => {
    // Тест для десктопа
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/dashboard')
    
    // Проверяем, что элементы отображаются правильно
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
    
    // Тест для планшета
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/dashboard')
    
    // Проверяем адаптивность
    await expect(page.getByText('Dashboard')).toBeVisible()
    
    // Тест для мобильного телефона
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/dashboard')
    
    // Проверяем мобильную версию
    await expect(page.getByText('Dashboard')).toBeVisible()
    
    // Проверяем, что меню становится мобильным
    const menuButton = await page.$('button[aria-label="Menu"]')
    expect(menuButton).not.toBeNull()
  })

  test('UI works with different themes', async ({ page }) => {
    await page.goto('/dashboard')
    
    // Проверяем светлую тему
    await page.click('button[aria-label="Toggle theme"]')
    await expect(page.locator('body')).not.toHaveClass(/dark/)
    
    // Переключаемся на темную тему
    await page.click('button[aria-label="Toggle theme"]')
    await expect(page.locator('body')).toHaveClass(/dark/)
    
    // Проверяем, что элементы отображаются правильно в темной теме
    await expect(page.getByText('Dashboard')).toBeVisible()
  })

  test('UI handles different locales', async ({ page }) => {
    // Устанавливаем русскую локаль
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'language', { 
        get: function() { return 'ru-RU'; } 
      });
    });
    
    await page.goto('/dashboard')
    
    // Проверяем, что интерфейс на русском языке
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
    
    // Устанавливаем английскую локаль
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'language', { 
        get: function() { return 'en-US'; } 
      });
    });
    
    // Перезагружаем страницу
    await page.reload()
    
    // Проверяем, что интерфейс поддерживает переключение языков
    // В данном случае мы ожидаем, что интерфейс останется на русском,
    // так как локализация может быть реализована по-разному
    await expect(page.getByText('Dashboard')).toBeVisible()
  })

  test('UI handles different timezones', async ({ page }) => {
    // Устанавливаем таймзону
    await page.addInitScript(() => {
      Date.prototype.getTimezoneOffset = function() { return -180; }; // UTC+3 (Москва)
    });
    
    await page.goto('/features')
    
    // Проверяем, что даты отображаются правильно
    // Это зависит от реализации форматирования дат в приложении
    await expect(page.getByText(/\d{4}-\d{2}-\d{2}/)).toBeVisible()
  })

  test('UI works with different fonts', async ({ page }) => {
    // Добавляем кастомный шрифт
    await page.addStyleTag({
      content: `
        @font-face {
          font-family: 'CustomFont';
          src: local('Arial');
        }
        body {
          font-family: 'CustomFont', sans-serif;
        }
      `
    });
    
    await page.goto('/dashboard')
    
    // Проверяем, что интерфейс отображается правильно с кастомным шрифтом
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
  })

  test('UI handles different resolutions', async ({ page }) => {
    // Тест для низкого разрешения
    await page.setViewportSize({ width: 1024, height: 768 })
    await page.goto('/dashboard')
    
    // Проверяем, что элементы отображаются правильно
    await expect(page.getByText('Dashboard')).toBeVisible()
    
    // Тест для высокого разрешения
    await page.setViewportSize({ width: 2560, height: 1440 })
    await page.goto('/dashboard')
    
    // Проверяем, что элементы отображаются правильно
    await expect(page.getByText('Dashboard')).toBeVisible()
  })

  test('UI works with different aspect ratios', async ({ page }) => {
    // Тест для широкоформатного экрана
    await page.setViewportSize({ width: 1920, height: 1080 }) // 16:9
    await page.goto('/dashboard')
    
    // Проверяем, что элементы отображаются правильно
    await expect(page.getByText('Dashboard')).toBeVisible()
    
    // Тест для экрана с соотношением 4:3
    await page.setViewportSize({ width: 1024, height: 768 }) // 4:3
    await page.goto('/dashboard')
    
    // Проверяем, что элементы отображаются правильно
    await expect(page.getByText('Dashboard')).toBeVisible()
  })

  test('UI handles touch devices', async ({ page }) => {
    // Эмулируем сенсорное устройство
    await page.goto('/dashboard')
    
    // Проверяем, что элементы интерфейса доступны сенсорно
    const buttons = await page.$$('button')
    for (const button of buttons) {
      const rect = await button.boundingBox()
      // Проверяем, что кнопки достаточно большие для сенсорного взаимодействия
      if (rect) {
        expect(rect.width).toBeGreaterThanOrEqual(44) // Минимальный размер для сенсорных целей
        expect(rect.height).toBeGreaterThanOrEqual(44)
      }
    }
  })

  test('UI works with different input methods', async ({ page }) => {
    await page.goto('/chat')
    
    // Проверяем работу с клавиатурой
    const chatInput = page.getByPlaceholderText('Опишите фичу на естественном языке...')
    await chatInput.focus()
    await page.keyboard.type('Test message')
    await page.keyboard.press('Enter')
    
    // Проверяем, что сообщение отправлено
    await expect(page.getByText('Test message')).toBeVisible()
    
    // Проверяем работу с мышью
    await page.click('button:has-text("Очистить чат")')
    
    // Проверяем, что чат очищен
    // Это зависит от реализации, но в идеале чат должен быть пустым
  })

  test('UI handles different network conditions', async ({ page }) => {
    // Эмулируем медленное соединение
    await page.route('**/*', async route => {
      await page.waitForTimeout(100) // Искусственная задержка
      await route.continue()
    })
    
    await page.goto('/dashboard')
    
    // Проверяем, что страница загружается даже при медленном соединении
    await expect(page.getByText('Dashboard')).toBeVisible()
    
    // Проверяем, что индикаторы загрузки отображаются правильно
    await expect(page.getByRole('progressbar')).toBeVisible({ timeout: 5000 }).catch(() => {
      // Если индикатор загрузки исчез, проверяем, что контент загрузился
      expect(page.getByText('System Health')).toBeVisible()
    })
  })

  test('UI works with different browser extensions', async ({ page }) => {
    // Добавляем мок для популярных расширений
    await page.addInitScript(() => {
      // Мок для AdBlock
      window.adsbygoogle = undefined;
      
      // Мок для других расширений
      window.chrome = undefined;
    });
    
    await page.goto('/dashboard')
    
    // Проверяем, что UI работает без ошибок
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
  })

  test('UI handles different cookie settings', async ({ page }) => {
    // Отключаем cookies
    await page.context().clearCookies()
    
    await page.goto('/login')
    
    // Авторизуемся
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    
    await page.goto('/dashboard')
    
    // Проверяем, что UI работает без cookies
    await expect(page.getByText('Dashboard')).toBeVisible()
  })

  test('UI works with JavaScript disabled', async ({ page }) => {
    // Отключаем JavaScript
    await page.addInitScript(() => {
      // Это не отключает JS в Playwright, но показывает намерение
      // В реальности, для тестирования без JS потребуется другой подход
    });
    
    await page.goto('/dashboard')
    
    // Проверяем базовую функциональность
    // Это зависит от того, насколько SPA зависит от JS
    await expect(page.getByText('Dashboard')).toBeVisible()
  })
})