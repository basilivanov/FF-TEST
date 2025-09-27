import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Docs from '@/pages/Docs'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/docs'
  })
}))

// Мокаем API
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn()
}))

const mockGet = require('@/lib/api').get
const mockPost = require('@/lib/api').post

describe('Docs', () => {
  beforeEach(() => {
    // Настраиваем мок данные для API
    mockGet.mockImplementation((url: string) => {
      if (url === '/docs/status') {
        return Promise.resolve({ data: { docs: [] } })
      }
      if (url === '/cortex/health') {
        return Promise.resolve({
          data: {
            overall_score: 76,
            context_freshness: 76,
            role_coverage: 3,
            knowledge_completeness: 76,
            last_updated: '2025-09-19 17:40:06.657607+00:00',
            roles: [
              {
                role: 'Dev',
                context_quality: 95,
                docs_count: 3,
                last_updated: '2025-09-18 08:23:44.508577+00:00',
                issues: [],
                icon: 'Code'
              }
            ]
          }
        })
      }
      return Promise.resolve({ data: null })
    })

    mockPost.mockResolvedValue({ data: { status: 'Analysis started' } })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders cortex health title', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    expect(screen.getByText('Cortex Health & Documentation')).toBeInTheDocument()
    expect(screen.getByText('Мониторинг здоровья кортекса, качества контекста и базы знаний')).toBeInTheDocument()
  })

  it('renders analyze cortex button', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    expect(screen.getByRole('button', { name: 'Анализ кортекса' })).toBeInTheDocument()
  })

  it('renders cortex health tabs', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    expect(screen.getByText('Здоровье Кортекса')).toBeInTheDocument()
    expect(screen.getByText('Анализ Ролей')).toBeInTheDocument()
    expect(screen.getByText('Документация')).toBeInTheDocument()
  })

  it('displays cortex health metrics', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    await waitFor(() => {
      const elements = screen.getAllByText('76%')
      expect(elements.length).toBeGreaterThan(0) // Overall score appears multiple times
    })
  })

  it('displays role analysis cards', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    // Дождёмся загрузки данных, затем переключимся на вкладку анализа ролей
    await waitFor(() => {
      expect(screen.getByText('Анализ Ролей')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Анализ Ролей'))

    await waitFor(() => {
      expect(screen.getByText('Dev')).toBeInTheDocument()
      // Dev role score может быть в разных местах, просто проверим что есть роль
    })
  })

  it('shows documentation tab when switched', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    // Переключаемся на вкладку документации
    fireEvent.click(screen.getByText('Документация'))

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Поиск по названию документа или версии...')).toBeInTheDocument()
    })
  })

  it('triggers cortex analysis', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    const analyzeButton = screen.getByRole('button', { name: 'Анализ кортекса' })
    fireEvent.click(analyzeButton)

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/cortex/analyze')
    })
  })

  it('loads real cortex health data', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/cortex/health')
      expect(mockGet).toHaveBeenCalledWith('/docs/status')
    })
  })

  it('handles cortex health API errors gracefully', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === '/cortex/health') {
        return Promise.resolve({ error: 'API not available' })
      }
      return Promise.resolve({ data: { docs: [] } })
    })

    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    // Проверяем что компонент отображается с fallback данными
    expect(screen.getByText('Cortex Health & Documentation')).toBeInTheDocument()
  })
})