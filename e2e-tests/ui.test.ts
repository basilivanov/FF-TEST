// e2e-tests/ui.test.ts
import { test, expect } from '@playwright/test'

test.describe('Feature Factory Admin UI E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Авторизация перед каждым тестом
    await page.goto('/')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
  })

  test('Dashboard page loads and displays data', async ({ page }) => {
    // Проверяем, что заголовок страницы правильный
    await expect(page).toHaveTitle(/Feature Factory/)
    
    // Проверяем наличие карточек дашборда
    await expect(page.getByText('System Health')).toBeVisible()
    await expect(page.getByText('Backlog')).toBeVisible()
    await expect(page.getByText('Recent Runs')).toBeVisible()
    await expect(page.getByText('LLM Budgets')).toBeVisible()
    await expect(page.getByText('Recent Errors')).toBeVisible()
    await expect(page.getByText('Docs')).toBeVisible()
    
    // Проверяем наличие баннера тестового окружения
    await expect(page.getByText('Тестовое окружение')).toBeVisible()
  })

  test('Features page loads and displays features', async ({ page }) => {
    // Переходим на страницу фич
    await page.click('text=Features')
    
    // Проверяем, что мы на правильной странице
    await expect(page.getByText('Features')).toBeVisible()
    await expect(page.getByText('Управление фичами и их жизненным циклом')).toBeVisible()
    
    // Проверяем наличие таблицы фич
    await expect(page.getByText('Название')).toBeVisible()
    await expect(page.getByText('Статус')).toBeVisible()
    await expect(page.getByText('Приоритет')).toBeVisible()
    await expect(page.getByText('Создано')).toBeVisible()
    await expect(page.getByText('Автор')).toBeVisible()
    await expect(page.getByText('Действия')).toBeVisible()
    
    // Проверяем наличие кнопки создания фичи
    await expect(page.getByRole('button', { name: 'Создать фичу' })).toBeVisible()
  })

  test('Feature detail page loads', async ({ page }) => {
    // Переходим на страницу фич
    await page.click('text=Features')
    
    // Кликаем на первую фичу в списке
    await page.click('text=ETL Pipeline Implementation')
    
    // Проверяем, что мы на странице деталей фичи
    await expect(page.getByText('ETL Pipeline Implementation')).toBeVisible()
    await expect(page.getByText('Детали фичи и управление её выполнением')).toBeVisible()
    
    // Проверяем наличие вкладок
    await expect(page.getByText('Задачи')).toBeVisible()
    await expect(page.getByText('История запусков')).toBeVisible()
  })

  test('Tasks page loads and displays tasks', async ({ page }) => {
    // Переходим на страницу задач
    await page.click('text=Tasks')
    
    // Проверяем, что мы на правильной странице
    await expect(page.getByText('Tasks')).toBeVisible()
    await expect(page.getByText('Управление задачами и их выполнением')).toBeVisible()
    
    // Проверяем наличие таблицы задач
    await expect(page.getByText('ID задачи')).toBeVisible()
    await expect(page.getByText('Фича')).toBeVisible()
    await expect(page.getByText('Роль')).toBeVisible()
    await expect(page.getByText('Содержимое')).toBeVisible()
    await expect(page.getByText('Статус')).toBeVisible()
    await expect(page.getByText('Попытки')).toBeVisible()
    await expect(page.getByText('Бюджет токенов')).toBeVisible()
    await expect(page.getByText('Расписание')).toBeVisible()
    await expect(page.getByText('Действия')).toBeVisible()
  })

  test('Runs page loads and displays runs', async ({ page }) => {
    // Переходим на страницу запусков
    await page.click('text=Runs')
    
    // Проверяем, что мы на правильной странице
    await expect(page.getByText('Runs')).toBeVisible()
    await expect(page.getByText('Управление запусками графов и их состоянием')).toBeVisible()
    
    // Проверяем наличие таблицы запусков
    await expect(page.getByText('ID запуска')).toBeVisible()
    await expect(page.getByText('Фича')).toBeVisible()
    await expect(page.getByText('Граф')).toBeVisible()
    await expect(page.getByText('Thread ID')).toBeVisible()
    await expect(page.getByText('Состояние')).toBeVisible()
    await expect(page.getByText('Статус')).toBeVisible()
    await expect(page.getByText('Последний чекпоинт')).toBeVisible()
    await expect(page.getByText('Действия')).toBeVisible()
  })

  test('Logs page loads and displays log stream', async ({ page }) => {
    // Переходим на страницу логов
    await page.click('text=Logs')
    
    // Проверяем, что мы на правильной странице
    await expect(page.getByText('Logs')).toBeVisible()
    await expect(page.getByText('Поток логов в реальном времени с фильтрацией')).toBeVisible()
    
    // Проверяем наличие элементов управления логами
    await expect(page.getByRole('button', { name: 'Пауза' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Очистить' })).toBeVisible()
  })

  test('Tokens page loads and displays token statistics', async ({ page }) => {
    // Переходим на страницу токенов
    await page.click('text=Tokens')
    
    // Проверяем, что мы на правильной странице
    await expect(page.getByText('Tokens')).toBeVisible()
    await expect(page.getByText('Сводка расхода токенов по ролям и моделям')).toBeVisible()
    
    // Проверяем наличие карточек статистики
    await expect(page.getByText('Входные токены')).toBeVisible()
    await expect(page.getByText('Выходные токены')).toBeVisible()
    await expect(page.getByText('Всего токенов')).toBeVisible()
    await expect(page.getByText('Стоимость ($)')).toBeVisible()
  })

  test('Docs page loads and displays documentation', async ({ page }) => {
    // Переходим на страницу документов
    await page.click('text=Docs')
    
    // Проверяем, что мы на правильной странице
    await expect(page.getByText('Docs')).toBeVisible()
    await expect(page.getByText('Управление документацией и ее актуальность')).toBeVisible()
    
    // Проверяем наличие таблицы документов
    await expect(page.getByText('Название документа')).toBeVisible()
    await expect(page.getByText('Версия')).toBeVisible()
    await expect(page.getByText('Хэш содержимого')).toBeVisible()
    await expect(page.getByText('Обновлено')).toBeVisible()
    await expect(page.getByText('Статус')).toBeVisible()
    await expect(page.getByText('Действия')).toBeVisible()
  })

  test('Settings page loads and displays settings', async ({ page }) => {
    // Переходим на страницу настроек
    await page.click('text=Settings')
    
    // Проверяем, что мы на правильной странице
    await expect(page.getByText('Settings')).toBeVisible()
    await expect(page.getByText('Настройки системы (только чтение в MVP)')).toBeVisible()
    
    // Проверяем наличие секций настроек
    await expect(page.getByText('Часовой пояс приложения')).toBeVisible()
    await expect(page.getByText('Расписания')).toBeVisible()
    await expect(page.getByText('API Keys')).toBeVisible()
    await expect(page.getByText('Идентификаторы')).toBeVisible()
  })

  test('Chat page loads and allows messaging', async ({ page }) => {
    // Переходим на страницу чата
    await page.click('text=Chat')
    
    // Проверяем, что мы на правильной странице
    await expect(page.getByText('Chat (Maintainer)')).toBeVisible()
    await expect(page.getByText('Ввод на естественном языке → генерация интента и плана → создание фичи')).toBeVisible()
    
    // Проверяем наличие элементов чата
    await expect(page.getByPlaceholderText('Опишите фичу на естественном языке...')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Send' })).toBeVisible()
  })

  test('Navigation works correctly', async ({ page }) => {
    // Проверяем навигацию по страницам
    const navItems = ['Dashboard', 'Features', 'Tasks', 'Runs', 'Logs', 'Tokens', 'Docs', 'Settings', 'Chat']
    
    for (const item of navItems) {
      await page.click(`text=${item}`)
      await expect(page.getByText(item)).toBeVisible()
    }
  })

  test('Responsive design works on mobile', async ({ page }) => {
    // Устанавливаем мобильное разрешение
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Проверяем, что навигация становится мобильной
    await expect(page.getByRole('button', { name: 'Menu' })).toBeVisible()
    
    // Открываем меню
    await page.click('button[aria-label="Menu"]')
    
    // Проверяем, что пункты меню видны
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('Features')).toBeVisible()
    await expect(page.getByText('Tasks')).toBeVisible()
    await expect(page.getByText('Runs')).toBeVisible()
    await expect(page.getByText('Logs')).toBeVisible()
    await expect(page.getByText('Tokens')).toBeVisible()
    await expect(page.getByText('Docs')).toBeVisible()
    await expect(page.getByText('Settings')).toBeVisible()
    await expect(page.getByText('Chat')).toBeVisible()
  })
})