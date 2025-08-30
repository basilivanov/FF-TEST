import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Runs from '@/pages/Runs'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/runs'
  })
}))

describe('Runs', () => {
  it('renders runs title', () => {
    render(
      <BrowserRouter>
        <Runs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Runs')).toBeInTheDocument()
    expect(screen.getByText('Управление запусками графов и их состоянием')).toBeInTheDocument()
  })

  it('renders refresh all button', () => {
    render(
      <BrowserRouter>
        <Runs />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Обновить все' })).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(
      <BrowserRouter>
        <Runs />
      </BrowserRouter>
    )
    
    expect(screen.getByPlaceholderText('Поиск по ID запуска, thread ID или содержимому состояния...')).toBeInTheDocument()
  })

  it('renders status filter badges', () => {
    render(
      <BrowserRouter>
        <Runs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
    expect(screen.getByText('DONE')).toBeInTheDocument()
    expect(screen.getByText('FAILED')).toBeInTheDocument()
  })

  it('renders runs table', () => {
    render(
      <BrowserRouter>
        <Runs />
      </BrowserRouter>
    )
    
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
    render(
      <BrowserRouter>
        <Runs />
      </BrowserRouter>
    )
    
    const runningBadge = screen.getByText('RUNNING')
    fireEvent.click(runningBadge)
    
    // Проверяем, что фильтр применился
    expect(runningBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows searching runs', () => {
    render(
      <BrowserRouter>
        <Runs />
      </BrowserRouter>
    )
    
    const searchInput = screen.getByPlaceholderText('Поиск по ID запуска, thread ID или содержимому состояния...')
    fireEvent.change(searchInput, { target: { value: 'run-001' } })
    
    // Проверяем, что значение ввода изменилось
    expect(searchInput).toHaveValue('run-001')
  })
})