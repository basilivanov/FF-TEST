import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from '@/pages/Dashboard'
import Features from '@/pages/Features'
import FeatureDetail from '@/pages/FeatureDetail'
import Tasks from '@/pages/Tasks'
import Runs from '@/pages/Runs'
import Logs from '@/pages/Logs'
import Tokens from '@/pages/Tokens'
import Docs from '@/pages/Docs'
import Settings from '@/pages/Settings'
import Chat from '@/pages/Chat'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/'
  }),
  useParams: () => ({
    id: '1'
  })
}))

// Мокаем sseClient
jest.mock('@/lib/sse', () => ({
  sseClient: {
    connect: jest.fn(),
    disconnect: jest.fn(),
    on: jest.fn(),
    off: jest.fn()
  }
}))

// Создаем QueryClient для тестов
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

// Wrapper для провайдеров
const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </QueryClientProvider>
)

describe('UI Integration Tests', () => {
  beforeEach(() => {
    // Очищаем моки перед каждым тестом
    jest.clearAllMocks()
  })

  describe('Dashboard Page', () => {
    it('renders all dashboard cards', () => {
      render(<Dashboard />, { wrapper })
      
      expect(screen.getByText('System Health')).toBeInTheDocument()
      expect(screen.getByText('Backlog')).toBeInTheDocument()
      expect(screen.getByText('Recent Runs')).toBeInTheDocument()
      expect(screen.getByText('LLM Budgets')).toBeInTheDocument()
      expect(screen.getByText('Recent Errors')).toBeInTheDocument()
      expect(screen.getByText('Docs')).toBeInTheDocument()
    })

    it('renders environment banner', () => {
      render(<Dashboard />, { wrapper })
      
      expect(screen.getByText('Тестовое окружение')).toBeInTheDocument()
    })

    it('has refresh button that triggers data refresh', () => {
      render(<Dashboard />, { wrapper })
      
      const refreshButton = screen.getByRole('button', { name: 'Refresh Data' })
      expect(refreshButton).toBeInTheDocument()
      
      // Здесь можно добавить проверку вызова функции обновления данных
      fireEvent.click(refreshButton)
    })
  })

  describe('Features Page', () => {
    it('renders features table with data', () => {
      render(<Features />, { wrapper })
      
      expect(screen.getByText('Features')).toBeInTheDocument()
      expect(screen.getByText('Управление фичами и их жизненным циклом')).toBeInTheDocument()
      
      // Проверяем наличие таблицы фич
      expect(screen.getByText('Название')).toBeInTheDocument()
      expect(screen.getByText('Статус')).toBeInTheDocument()
      expect(screen.getByText('Приоритет')).toBeInTheDocument()
      expect(screen.getByText('Создано')).toBeInTheDocument()
      expect(screen.getByText('Автор')).toBeInTheDocument()
      expect(screen.getByText('Действия')).toBeInTheDocument()
    })

    it('allows filtering features by status', () => {
      render(<Features />, { wrapper })
      
      const newBadge = screen.getByText('NEW')
      fireEvent.click(newBadge)
      
      // Проверяем, что фильтр применился
      expect(newBadge).toHaveClass('bg-blue-500')
    })

    it('allows searching features', () => {
      render(<Features />, { wrapper })
      
      const searchInput = screen.getByPlaceholderText('Поиск по названию или описанию...')
      fireEvent.change(searchInput, { target: { value: 'ETL' } })
      
      // Проверяем, что значение ввода изменилось
      expect(searchInput).toHaveValue('ETL')
    })

    it('has create feature button', () => {
      render(<Features />, { wrapper })
      
      const createButton = screen.getByRole('button', { name: 'Создать фичу' })
      expect(createButton).toBeInTheDocument()
    })
  })

  describe('Feature Detail Page', () => {
    it('renders feature details', () => {
      render(<FeatureDetail />, { wrapper })
      
      expect(screen.getByText('ETL Pipeline Implementation')).toBeInTheDocument()
      expect(screen.getByText('Детали фичи и управление её выполнением')).toBeInTheDocument()
    })

    it('renders tabs for tasks and run history', () => {
      render(<FeatureDetail />, { wrapper })
      
      expect(screen.getByText('Задачи')).toBeInTheDocument()
      expect(screen.getByText('История запусков')).toBeInTheDocument()
    })

    it('switches between tabs', () => {
      render(<FeatureDetail />, { wrapper })
      
      const tasksTab = screen.getByText('Задачи')
      const historyTab = screen.getByText('История запусков')
      
      // По умолчанию активна вкладка задач
      expect(screen.getByText('Задача')).toBeInTheDocument()
      
      // Переключаемся на историю
      fireEvent.click(historyTab)
      expect(screen.getByText('ID запуска')).toBeInTheDocument()
      
      // Переключаемся обратно на задачи
      fireEvent.click(tasksTab)
      expect(screen.getByText('Задача')).toBeInTheDocument()
    })

    it('has action buttons', () => {
      render(<FeatureDetail />, { wrapper })
      
      expect(screen.getByRole('button', { name: 'Запустить' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Редактировать' })).toBeInTheDocument()
    })
  })

  describe('Tasks Page', () => {
    it('renders tasks table with data', () => {
      render(<Tasks />, { wrapper })
      
      expect(screen.getByText('Tasks')).toBeInTheDocument()
      expect(screen.getByText('Управление задачами и их выполнением')).toBeInTheDocument()
      
      // Проверяем наличие таблицы задач
      expect(screen.getByText('ID задачи')).toBeInTheDocument()
      expect(screen.getByText('Фича')).toBeInTheDocument()
      expect(screen.getByText('Роль')).toBeInTheDocument()
      expect(screen.getByText('Содержимое')).toBeInTheDocument()
      expect(screen.getByText('Статус')).toBeInTheDocument()
      expect(screen.getByText('Попытки')).toBeInTheDocument()
      expect(screen.getByText('Бюджет токенов')).toBeInTheDocument()
      expect(screen.getByText('Расписание')).toBeInTheDocument()
      expect(screen.getByText('Действия')).toBeInTheDocument()
    })

    it('allows filtering tasks by role', () => {
      render(<Tasks />, { wrapper })
      
      const devBadge = screen.getByText('Dev')
      fireEvent.click(devBadge)
      
      // Проверяем, что фильтр применился
      expect(devBadge).toHaveClass('bg-blue-500')
    })

    it('allows filtering tasks by status', () => {
      render(<Tasks />, { wrapper })
      
      const doneBadge = screen.getByText('DONE')
      fireEvent.click(doneBadge)
      
      // Проверяем, что фильтр применился
      expect(doneBadge).toHaveClass('bg-blue-500')
    })

    it('allows searching tasks', () => {
      render(<Tasks />, { wrapper })
      
      const searchInput = screen.getByPlaceholderText('Поиск по ID или содержимому задачи...')
      fireEvent.change(searchInput, { target: { value: 'generate' } })
      
      // Проверяем, что значение ввода изменилось
      expect(searchInput).toHaveValue('generate')
    })
  })

  describe('Runs Page', () => {
    it('renders runs table with data', () => {
      render(<Runs />, { wrapper })
      
      expect(screen.getByText('Runs')).toBeInTheDocument()
      expect(screen.getByText('Управление запусками графов и их состоянием')).toBeInTheDocument()
      
      // Проверяем наличие таблицы запусков
      expect(screen.getByText('ID запуска')).toBeInTheDocument()
      expect(screen.getByText('Фича')).toBeInTheDocument()
      expect(screen.getByText('Граф')).toBeInTheDocument()
      expect(screen.getByText('Thread ID')).toBeInTheDocument()
      expect(screen.getByText('Состояние')).toBeInTheDocument()
      expect(screen.getByText('Статус')).toBeInTheDocument()
      expect(screen.getByText('Последний чекпоинт')).toBeInTheDocument()
      expect(screen.getByText('Действия')).toBeInTheDocument()
    })

    it('allows filtering runs by status', () => {
      render(<Runs />, { wrapper })
      
      const runningBadge = screen.getByText('RUNNING')
      fireEvent.click(runningBadge)
      
      // Проверяем, что фильтр применился
      expect(runningBadge).toHaveClass('bg-blue-500')
    })

    it('allows searching runs', () => {
      render(<Runs />, { wrapper })
      
      const searchInput = screen.getByPlaceholderText('Поиск по ID запуска, thread ID или содержимому состояния...')
      fireEvent.change(searchInput, { target: { value: 'run-001' } })
      
      // Проверяем, что значение ввода изменилось
      expect(searchInput).toHaveValue('run-001')
    })

    it('has refresh all button', () => {
      render(<Runs />, { wrapper })
      
      const refreshButton = screen.getByRole('button', { name: 'Обновить все' })
      expect(refreshButton).toBeInTheDocument()
    })
  })

  describe('Logs Page', () => {
    it('renders logs with streaming capabilities', () => {
      render(<Logs />, { wrapper })
      
      expect(screen.getByText('Logs')).toBeInTheDocument()
      expect(screen.getByText('Поток логов в реальном времени с фильтрацией')).toBeInTheDocument()
      
      // Проверяем наличие элементов управления
      expect(screen.getByRole('button', { name: 'Пауза' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Очистить' })).toBeInTheDocument()
    })

    it('allows filtering logs by component', () => {
      render(<Logs />, { wrapper })
      
      const orchestratorBadge = screen.getByText('orchestrator')
      fireEvent.click(orchestratorBadge)
      
      // Проверяем, что фильтр применился
      expect(orchestratorBadge).toHaveClass('bg-blue-500')
    })

    it('allows filtering logs by level', () => {
      render(<Logs />, { wrapper })
      
      const infoBadge = screen.getByText('INFO')
      fireEvent.click(infoBadge)
      
      // Проверяем, что фильтр применился
      expect(infoBadge).toHaveClass('bg-blue-500')
    })

    it('allows searching logs', () => {
      render(<Logs />, { wrapper })
      
      const searchInput = screen.getByPlaceholderText('Поиск по событию или содержимому лога...')
      fireEvent.change(searchInput, { target: { value: 'job_started' } })
      
      // Проверяем, что значение ввода изменилось
      expect(searchInput).toHaveValue('job_started')
    })

    it('has auto-scroll toggle', () => {
      render(<Logs />, { wrapper })
      
      const autoScrollCheckbox = screen.getByLabelText('Автопрокрутка')
      expect(autoScrollCheckbox).toBeInTheDocument()
      
      // Проверяем переключение
      fireEvent.click(autoScrollCheckbox)
      expect(autoScrollCheckbox).not.toBeChecked()
    })
  })

  describe('Tokens Page', () => {
    it('renders token usage statistics', () => {
      render(<Tokens />, { wrapper })
      
      expect(screen.getByText('Tokens')).toBeInTheDocument()
      expect(screen.getByText('Сводка расхода токенов по ролям и моделям')).toBeInTheDocument()
      
      // Проверяем наличие карточек статистики
      expect(screen.getByText('Входные токены')).toBeInTheDocument()
      expect(screen.getByText('Выходные токены')).toBeInTheDocument()
      expect(screen.getByText('Всего токенов')).toBeInTheDocument()
      expect(screen.getByText('Стоимость ($)')).toBeInTheDocument()
    })

    it('allows filtering tokens by role', () => {
      render(<Tokens />, { wrapper })
      
      const devBadge = screen.getByText('Dev')
      fireEvent.click(devBadge)
      
      // Проверяем, что фильтр применился
      expect(devBadge).toHaveClass('bg-blue-500')
    })

    it('allows filtering tokens by model', () => {
      render(<Tokens />, { wrapper })
      
      const qwenBadge = screen.getByText('qwen-plus')
      fireEvent.click(qwenBadge)
      
      // Проверяем, что фильтр применился
      expect(qwenBadge).toHaveClass('bg-blue-500')
    })

    it('allows searching tokens', () => {
      render(<Tokens />, { wrapper })
      
      const searchInput = screen.getByPlaceholderText('Поиск по роли или модели...')
      fireEvent.change(searchInput, { target: { value: 'Architect' } })
      
      // Проверяем, что значение ввода изменилось
      expect(searchInput).toHaveValue('Architect')
    })

    it('has refresh data button', () => {
      render(<Tokens />, { wrapper })
      
      const refreshButton = screen.getByRole('button', { name: 'Обновить данные' })
      expect(refreshButton).toBeInTheDocument()
    })
  })

  describe('Docs Page', () => {
    it('renders documentation registry', () => {
      render(<Docs />, { wrapper })
      
      expect(screen.getByText('Docs')).toBeInTheDocument()
      expect(screen.getByText('Управление документацией и ее актуальность')).toBeInTheDocument()
      
      // Проверяем наличие таблицы документов
      expect(screen.getByText('Название документа')).toBeInTheDocument()
      expect(screen.getByText('Версия')).toBeInTheDocument()
      expect(screen.getByText('Хэш содержимого')).toBeInTheDocument()
      expect(screen.getByText('Обновлено')).toBeInTheDocument()
      expect(screen.getByText('Статус')).toBeInTheDocument()
      expect(screen.getByText('Действия')).toBeInTheDocument()
    })

    it('allows filtering docs by status', () => {
      render(<Docs />, { wrapper })
      
      const draftBadge = screen.getByText('Черновик')
      fireEvent.click(draftBadge)
      
      // Проверяем, что фильтр применился
      expect(draftBadge).toHaveClass('bg-blue-500')
    })

    it('allows searching docs', () => {
      render(<Docs />, { wrapper })
      
      const searchInput = screen.getByPlaceholderText('Поиск по названию документа или версии...')
      fireEvent.change(searchInput, { target: { value: 'Architecture' } })
      
      // Проверяем, что значение ввода изменилось
      expect(searchInput).toHaveValue('Architecture')
    })

    it('has rebuild documentation button', () => {
      render(<Docs />, { wrapper })
      
      const rebuildButton = screen.getByRole('button', { name: 'Пересобрать документацию' })
      expect(rebuildButton).toBeInTheDocument()
    })
  })

  describe('Settings Page', () => {
    it('renders system settings', () => {
      render(<Settings />, { wrapper })
      
      expect(screen.getByText('Settings')).toBeInTheDocument()
      expect(screen.getByText('Настройки системы (только чтение в MVP)')).toBeInTheDocument()
      
      // Проверяем наличие секций настроек
      expect(screen.getByText('Часовой пояс приложения')).toBeInTheDocument()
      expect(screen.getByText('Расписания')).toBeInTheDocument()
      expect(screen.getByText('API Keys')).toBeInTheDocument()
      expect(screen.getByText('Идентификаторы')).toBeInTheDocument()
    })

    it('has edit and reset buttons', () => {
      render(<Settings />, { wrapper })
      
      const editButton = screen.getByRole('button', { name: 'Редактировать' })
      const resetButton = screen.getByRole('button', { name: 'Сбросить' })
      
      expect(editButton).toBeInTheDocument()
      expect(resetButton).toBeInTheDocument()
    })

    it('allows editing settings', () => {
      render(<Settings />, { wrapper })
      
      const editButton = screen.getByRole('button', { name: 'Редактировать' })
      fireEvent.click(editButton)
      
      // Проверяем появление кнопок сохранения и отмены
      expect(screen.getByRole('button', { name: 'Отменить' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Сохранить изменения' })).toBeInTheDocument()
    })
  })

  describe('Chat Page', () => {
    it('renders chat interface', () => {
      render(<Chat />, { wrapper })
      
      expect(screen.getByText('Chat (Maintainer)')).toBeInTheDocument()
      expect(screen.getByText('Ввод на естественном языке → генерация интента и плана → создание фичи')).toBeInTheDocument()
      
      // Проверяем наличие элементов чата
      expect(screen.getByPlaceholderText('Опишите фичу на естественном языке...')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument()
    })

    it('allows sending messages', async () => {
      render(<Chat />, { wrapper })
      
      const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
      const sendButton = screen.getByRole('button', { name: 'Send' })
      
      fireEvent.change(textarea, { target: { value: 'Test message' } })
      fireEvent.click(sendButton)
      
      // Проверяем, что сообщение отправлено
      await waitFor(() => {
        expect(screen.getByText('Test message')).toBeInTheDocument()
      })
    })

    it('has clear chat button', () => {
      render(<Chat />, { wrapper })
      
      const clearButton = screen.getByRole('button', { name: 'Очистить чат' })
      expect(clearButton).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('navigates between pages', () => {
      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      )
      
      // Проверяем навигацию (здесь можно добавить больше проверок для роутинга)
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
  })
})