// performance-tests/ui-performance.test.ts
import { test, expect } from '@playwright/test'

test.describe('Feature Factory Admin UI Performance Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Увеличиваем таймаут для тестов производительности
    test.setTimeout(60000)
    
    // Авторизация перед каждым тестом
    await page.goto('/')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
  })

  test('Dashboard page loads within acceptable time', async ({ page }) => {
    // Измеряем время загрузки страницы
    const startTime = Date.now()
    await page.goto('/')
    const loadTime = Date.now() - startTime
    
    // Проверяем, что страница загрузилась за приемлемое время
    expect(loadTime).toBeLessThan(3000) // 3 секунды
    
    // Проверяем, что основные элементы страницы загружены
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('System Health')).toBeVisible()
  })

  test('Features page loads and renders large dataset efficiently', async ({ page }) => {
    // Переходим на страницу фич
    await page.goto('/features')
    
    // Измеряем время загрузки таблицы
    const startTime = Date.now()
    await expect(page.getByText('Features')).toBeVisible()
    const loadTime = Date.now() - startTime
    
    // Проверяем, что страница загрузилась за приемлемое время
    expect(loadTime).toBeLessThan(2000) // 2 секунды
    
    // Проверяем, что таблица отрендерилась
    await expect(page.getByText('Название')).toBeVisible()
    await expect(page.getByText('Статус')).toBeVisible()
  })

  test('Tasks page handles filtering efficiently', async ({ page }) => {
    // Переходим на страницу задач
    await page.goto('/tasks')
    
    // Измеряем время применения фильтра
    const startTime = Date.now()
    await page.click('text=Dev')
    await page.click('text=DONE')
    const filterTime = Date.now() - startTime
    
    // Проверяем, что фильтрация прошла за приемлемое время
    expect(filterTime).toBeLessThan(500) // 500 миллисекунд
    
    // Проверяем, что таблица обновилась
    await expect(page.getByText('ID задачи')).toBeVisible()
  })

  test('Logs page handles streaming efficiently', async ({ page }) => {
    // Переходим на страницу логов
    await page.goto('/logs')
    
    // Измеряем время загрузки потока логов
    const startTime = Date.now()
    await expect(page.getByText('Logs')).toBeVisible()
    const loadTime = Date.now() - startTime
    
    // Проверяем, что страница загрузилась за приемлемое время
    expect(loadTime).toBeLessThan(2000) // 2 секунды
    
    // Проверяем, что элементы управления логами присутствуют
    await expect(page.getByRole('button', { name: 'Пауза' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Очистить' })).toBeVisible()
  })

  test('Tokens page loads charts efficiently', async ({ page }) => {
    // Переходим на страницу токенов
    await page.goto('/tokens')
    
    // Измеряем время загрузки диаграмм
    const startTime = Date.now()
    await expect(page.getByText('Tokens')).toBeVisible()
    const loadTime = Date.now() - startTime
    
    // Проверяем, что страница загрузилась за приемлемое время
    expect(loadTime).toBeLessThan(2000) // 2 секунды
    
    // Проверяем, что карточки статистики загрузились
    await expect(page.getByText('Входные токены')).toBeVisible()
    await expect(page.getByText('Выходные токены')).toBeVisible()
  })

  test('Docs page handles search efficiently', async ({ page }) => {
    // Переходим на страницу документов
    await page.goto('/docs')
    
    // Измеряем время поиска
    const searchInput = page.getByPlaceholderText('Поиск по названию документа или версии...')
    const startTime = Date.now()
    await searchInput.fill('Architecture')
    await searchInput.press('Enter')
    const searchTime = Date.now() - startTime
    
    // Проверяем, что поиск прошел за приемлемое время
    expect(searchTime).toBeLessThan(1000) // 1 секунда
    
    // Проверяем, что результаты поиска отобразились
    await expect(page.getByText('Architecture')).toBeVisible()
  })

  test('Navigation between pages is fast', async ({ page }) => {
    // Переходим на главную страницу
    await page.goto('/')
    
    // Измеряем время перехода между страницами
    const navItems = ['Features', 'Tasks', 'Runs', 'Logs', 'Tokens', 'Docs', 'Settings', 'Chat']
    
    for (const item of navItems) {
      const startTime = Date.now()
      await page.click(`text=${item}`)
      const loadTime = Date.now() - startTime
      
      // Проверяем, что переход занял приемлемое время
      expect(loadTime).toBeLessThan(1000) // 1 секунда
      
      // Проверяем, что страница загрузилась
      await expect(page.getByText(item)).toBeVisible()
    }
  })

  test('UI maintains responsiveness under stress', async ({ page }) => {
    // Переходим на страницу фич
    await page.goto('/features')
    
    // Выполняем несколько последовательных действий
    const actions = [
      () => page.click('text=NEW'),
      () => page.click('text=PLANNED'),
      () => page.fill('input[placeholder="Поиск по названию или описанию..."]', 'ETL'),
      () => page.click('text=Dev'),
      () => page.click('text=QA'),
      () => page.click('button[aria-label="Refresh Data"]'),
    ]
    
    // Измеряем время выполнения всех действий
    const startTime = Date.now()
    for (const action of actions) {
      await action()
      // Небольшая пауза между действиями
      await page.waitForTimeout(100)
    }
    const totalTime = Date.now() - startTime
    
    // Проверяем, что все действия заняли приемлемое время
    expect(totalTime).toBeLessThan(5000) // 5 секунд
    
    // Проверяем, что интерфейс остался отзывчивым
    await expect(page.getByText('Features')).toBeVisible()
  })
})