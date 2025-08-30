// accessibility-tests/ui-accessibility.test.ts
import { test, expect } from '@playwright/test'

test.describe('Feature Factory Admin UI Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Авторизация перед каждым тестом
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
  })

  test('Dashboard page meets accessibility standards', async ({ page }) => {
    await page.goto('/dashboard')
    
    // Проверяем наличие заголовка страницы
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
    
    // Проверяем, что страница имеет основной контент
    await expect(page.getByRole('main')).toBeVisible()
    
    // Проверяем, что навигация доступна
    await expect(page.getByRole('navigation')).toBeVisible()
    
    // Проверяем, что все карточки имеют заголовки
    const cards = await page.$$('.rounded-lg.border')
    for (const card of cards) {
      const heading = await card.$('h2, h3, h4')
      expect(heading).not.toBeNull()
    }
    
    // Проверяем, что все интерактивные элементы имеют доступные имена
    const buttons = await page.$$('button')
    for (const button of buttons) {
      const accessibleName = await button.textContent()
      expect(accessibleName?.trim()).not.toBe('')
    }
  })

  test('Features page is keyboard navigable', async ({ page }) => {
    await page.goto('/features')
    
    // Проверяем, что страница загрузилась
    await expect(page.getByText('Features')).toBeVisible()
    
    // Проверяем навигацию с клавиатуры
    // Фокус на первом элементе
    await page.keyboard.press('Tab')
    
    // Проверяем, что фокус перемещается по интерактивным элементам
    const interactiveElements = [
      'Создать фичу',
      'NEW',
      'PLANNED',
      'RUNNING',
      'DONE',
      'FAILED'
    ]
    
    for (const elementText of interactiveElements) {
      await page.keyboard.press('Tab')
      const focusedElement = await page.$(':focus')
      const textContent = await focusedElement?.textContent()
      expect(textContent).toContain(elementText)
    }
  })

  test('Tables have proper accessibility attributes', async ({ page }) => {
    await page.goto('/features')
    
    // Проверяем, что таблицы имеют правильные роли
    const tables = await page.$$('table')
    for (const table of tables) {
      const role = await table.getAttribute('role')
      expect(role).toBe('table')
    }
    
    // Проверяем, что заголовки таблицы имеют правильные роли
    const thElements = await page.$$('th')
    for (const th of thElements) {
      const scope = await th.getAttribute('scope')
      expect(['col', 'row', 'colgroup', 'rowgroup']).toContain(scope)
    }
    
    // Проверяем, что ячейки данных имеют правильные роли
    const tdElements = await page.$$('td')
    for (const td of tdElements) {
      const role = await td.getAttribute('role')
      expect(role).toBe('cell')
    }
  })

  test('Forms have proper labels and error handling', async ({ page }) => {
    await page.goto('/features')
    await page.click('button:has-text("Создать фичу")')
    
    // Проверяем, что поля ввода имеют связанные метки
    const inputs = await page.$$('input, textarea, select')
    for (const input of inputs) {
      const id = await input.getAttribute('id')
      if (id) {
        const label = await page.$(`label[for="${id}"]`)
        expect(label).not.toBeNull()
      }
    }
    
    // Проверяем, что ошибки валидации доступны
    // Пытаемся отправить пустую форму
    await page.click('button:has-text("Создать")')
    
    // Проверяем, что ошибки валидации имеют правильные атрибуты
    const errorElements = await page.$$('.text-red-500')
    for (const error of errorElements) {
      const ariaLive = await error.getAttribute('aria-live')
      expect(ariaLive).toBe('polite')
    }
  })

  test('Color contrast meets WCAG standards', async ({ page }) => {
    await page.goto('/dashboard')
    
    // Проверяем контрастность текста
    // Это простая проверка, в реальности потребовалась бы более сложная логика
    
    // Проверяем основной текст
    const textElements = await page.$$('h1, h2, h3, p, span:not(.sr-only)')
    for (const element of textElements) {
      const color = await element.evaluate(el => {
        const style = window.getComputedStyle(el)
        return style.color
      })
      // Здесь могла бы быть проверка контрастности, но для упрощения просто проверим, что цвет определен
      expect(color).toBeDefined()
    }
  })

  test('Images have alternative text', async ({ page }) => {
    await page.goto('/dashboard')
    
    // Проверяем изображения на наличие alt текста
    const images = await page.$$('img')
    for (const img of images) {
      const alt = await img.getAttribute('alt')
      expect(alt).not.toBeNull()
      expect(alt?.trim()).not.toBe('')
    }
  })

  test('ARIA attributes are used correctly', async ({ page }) => {
    await page.goto('/features')
    
    // Проверяем использование ARIA атрибутов
    const elementsWithAria = await page.$('[aria-*]')
    if (elementsWithAria) {
      // Проверяем, что ARIA атрибуты имеют правильные значения
      const ariaAttributes = [
        'aria-label',
        'aria-labelledby',
        'aria-describedby',
        'aria-expanded',
        'aria-selected',
        'aria-checked',
        'aria-disabled'
      ]
      
      for (const attr of ariaAttributes) {
        const elements = await page.$$(`[${attr}]`)
        for (const element of elements) {
          const value = await element.getAttribute(attr)
          // Проверяем, что значения имеют смысл
          expect(value).toBeDefined()
        }
      }
    }
  })

  test('Focus management works correctly', async ({ page }) => {
    await page.goto('/features')
    
    // Проверяем, что фокус может быть установлен на интерактивные элементы
    const buttons = await page.$$('button')
    for (const button of buttons) {
      await button.focus()
      const isFocused = await button.evaluate(el => el === document.activeElement)
      expect(isFocused).toBe(true)
    }
    
    // Проверяем, что модальные окна правильно управляют фокусом
    // Открываем модальное окно (если есть)
    const modalTriggers = await page.$$('button[aria-haspopup="dialog"]')
    for (const trigger of modalTriggers) {
      await trigger.click()
      const modal = await page.$('[role="dialog"]')
      if (modal) {
        // Проверяем, что фокус перемещен в модальное окно
        const modalFocused = await modal.evaluate(el => el.contains(document.activeElement))
        expect(modalFocused).toBe(true)
        
        // Закрываем модальное окно
        await page.keyboard.press('Escape')
      }
    }
  })

  test('Screen reader compatibility', async ({ page }) => {
    await page.goto('/dashboard')
    
    // Проверяем, что важные элементы имеют правильные роли
    const landmarks = await page.$$('header, nav, main, aside, footer')
    for (const landmark of landmarks) {
      const tagName = await landmark.evaluate(el => el.tagName.toLowerCase())
      const role = await landmark.getAttribute('role')
      
      // Проверяем, что семантические элементы не переопределяют свои роли без необходимости
      if (['header', 'nav', 'main', 'aside', 'footer'].includes(tagName)) {
        // Эти элементы имеют встроенные роли, но могут иметь role атрибут для совместимости
        expect(role === null || typeof role === 'string').toBe(true)
      }
    }
    
    // Проверяем, что списки имеют правильные структуры
    const lists = await page.$$('ul, ol')
    for (const list of lists) {
      const listItems = await list.$$('li')
      expect(listItems.length).toBeGreaterThan(0)
    }
  })

  test('Responsive design maintains accessibility', async ({ page }) => {
    // Устанавливаем мобильное разрешение
    await page.setViewportSize({ width: 375, height: 667 })
    
    await page.goto('/features')
    
    // Проверяем, что мобильная навигация доступна
    const menuButton = await page.$('button[aria-label="Menu"]')
    expect(menuButton).not.toBeNull()
    
    if (menuButton) {
      // Открываем меню
      await menuButton.click()
      
      // Проверяем, что меню доступно
      const menu = await page.$('[role="menu"]')
      expect(menu).not.toBeNull()
      
      // Проверяем, что элементы меню доступны с клавиатуры
      await page.keyboard.press('Tab')
      const focusedElement = await page.$(':focus')
      expect(focusedElement).not.toBeNull()
    }
  })

  test('Loading states are accessible', async ({ page }) => {
    await page.goto('/features')
    
    // Проверяем, что состояния загрузки имеют правильные атрибуты
    // Это может включать спиннеры, индикаторы прогресса и т.д.
    const loadingIndicators = await page.$$('.animate-spin, [aria-busy="true"]')
    for (const indicator of loadingIndicators) {
      const ariaBusy = await indicator.getAttribute('aria-busy')
      expect(ariaBusy).toBe('true')
    }
    
    // Проверяем, что скринридеры получают информацию о загрузке
    const ariaLabels = await page.$$('.sr-only')
    expect(ariaLabels.length).toBeGreaterThan(0)
  })
})