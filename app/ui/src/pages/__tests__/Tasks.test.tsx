import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Tasks from '@/pages/Tasks'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/tasks'
  })
}))

describe('Tasks', () => {
  it('renders tasks title', () => {
    render(
      <BrowserRouter>
        <Tasks />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Tasks')).toBeInTheDocument()
    expect(screen.getByText('Управление задачами и их выполнением')).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(
      <BrowserRouter>
        <Tasks />
      </BrowserRouter>
    )
    
    expect(screen.getByPlaceholderText('Поиск по ID или содержимому задачи...')).toBeInTheDocument()
  })

  it('renders role filter badges', () => {
    render(
      <BrowserRouter>
        <Tasks />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('Architect')).toBeInTheDocument()
    expect(screen.getByText('Dev')).toBeInTheDocument()
    expect(screen.getByText('QA')).toBeInTheDocument()
    expect(screen.getByText('Scribe')).toBeInTheDocument()
    expect(screen.getByText('Maintainer')).toBeInTheDocument()
  })

  it('renders status filter badges', () => {
    render(
      <BrowserRouter>
        <Tasks />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('NEW')).toBeInTheDocument()
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
    expect(screen.getByText('DONE')).toBeInTheDocument()
    expect(screen.getByText('RETRYABLE_ERROR')).toBeInTheDocument()
    expect(screen.getByText('FAILED')).toBeInTheDocument()
    expect(screen.getByText('WAIT_BUDGET')).toBeInTheDocument()
  })

  it('renders tasks table', () => {
    render(
      <BrowserRouter>
        <Tasks />
      </BrowserRouter>
    )
    
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
    render(
      <BrowserRouter>
        <Tasks />
      </BrowserRouter>
    )
    
    const devBadge = screen.getByText('Dev')
    fireEvent.click(devBadge)
    
    // Проверяем, что фильтр применился
    expect(devBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows filtering tasks by status', () => {
    render(
      <BrowserRouter>
        <Tasks />
      </BrowserRouter>
    )
    
    const doneBadge = screen.getByText('DONE')
    fireEvent.click(doneBadge)
    
    // Проверяем, что фильтр применился
    expect(doneBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows searching tasks', () => {
    render(
      <BrowserRouter>
        <Tasks />
      </BrowserRouter>
    )
    
    const searchInput = screen.getByPlaceholderText('Поиск по ID или содержимому задачи...')
    fireEvent.change(searchInput, { target: { value: 'generate' } })
    
    // Проверяем, что значение ввода изменилось
    expect(searchInput).toHaveValue('generate')
  })
})