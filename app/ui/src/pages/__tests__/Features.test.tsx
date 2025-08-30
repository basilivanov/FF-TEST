import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Features from '@/pages/Features'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/features'
  })
}))

describe('Features', () => {
  it('renders features title', () => {
    render(
      <BrowserRouter>
        <Features />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Features')).toBeInTheDocument()
    expect(screen.getByText('Управление фичами и их жизненным циклом')).toBeInTheDocument()
  })

  it('renders create feature button', () => {
    render(
      <BrowserRouter>
        <Features />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Создать фичу' })).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(
      <BrowserRouter>
        <Features />
      </BrowserRouter>
    )
    
    expect(screen.getByPlaceholderText('Поиск по названию или описанию...')).toBeInTheDocument()
  })

  it('renders status filter badges', () => {
    render(
      <BrowserRouter>
        <Features />
      </BrowserRouter>
    )
    
    expect(screen.getByText('NEW')).toBeInTheDocument()
    expect(screen.getByText('PLANNED')).toBeInTheDocument()
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
    expect(screen.getByText('DONE')).toBeInTheDocument()
    expect(screen.getByText('FAILED')).toBeInTheDocument()
  })

  it('renders features table', () => {
    render(
      <BrowserRouter>
        <Features />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Название')).toBeInTheDocument()
    expect(screen.getByText('Статус')).toBeInTheDocument()
    expect(screen.getByText('Приоритет')).toBeInTheDocument()
    expect(screen.getByText('Создано')).toBeInTheDocument()
    expect(screen.getByText('Автор')).toBeInTheDocument()
    expect(screen.getByText('Действия')).toBeInTheDocument()
  })

  it('allows filtering features by status', () => {
    render(
      <BrowserRouter>
        <Features />
      </BrowserRouter>
    )
    
    const newBadge = screen.getByText('NEW')
    fireEvent.click(newBadge)
    
    // Проверяем, что фильтр применился
    expect(newBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows searching features', () => {
    render(
      <BrowserRouter>
        <Features />
      </BrowserRouter>
    )
    
    const searchInput = screen.getByPlaceholderText('Поиск по названию или описанию...')
    fireEvent.change(searchInput, { target: { value: 'ETL' } })
    
    // Проверяем, что значение ввода изменилось
    expect(searchInput).toHaveValue('ETL')
  })
})