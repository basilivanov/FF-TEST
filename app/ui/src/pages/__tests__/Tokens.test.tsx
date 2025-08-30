import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Tokens from '@/pages/Tokens'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/tokens'
  })
}))

describe('Tokens', () => {
  it('renders tokens title', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Tokens')).toBeInTheDocument()
    expect(screen.getByText('Сводка расхода токенов по ролям и моделям')).toBeInTheDocument()
  })

  it('renders refresh button', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Обновить данные' })).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    expect(screen.getByPlaceholderText('Поиск по роли или модели...')).toBeInTheDocument()
  })

  it('renders role filter badges', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('Architect')).toBeInTheDocument()
    expect(screen.getByText('Dev')).toBeInTheDocument()
    expect(screen.getByText('QA')).toBeInTheDocument()
    expect(screen.getByText('Scribe')).toBeInTheDocument()
    expect(screen.getByText('Maintainer')).toBeInTheDocument()
  })

  it('renders model filter badges', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('claude-3-opus')).toBeInTheDocument()
    expect(screen.getByText('claude-3-sonnet')).toBeInTheDocument()
    expect(screen.getByText('qwen-plus')).toBeInTheDocument()
    expect(screen.getByText('gpt-4')).toBeInTheDocument()
    expect(screen.getByText('gemini-pro')).toBeInTheDocument()
  })

  it('renders summary cards', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Входные токены')).toBeInTheDocument()
    expect(screen.getByText('Выходные токены')).toBeInTheDocument()
    expect(screen.getByText('Всего токенов')).toBeInTheDocument()
    expect(screen.getByText('Стоимость ($)')).toBeInTheDocument()
  })

  it('renders token usage table', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Роль')).toBeInTheDocument()
    expect(screen.getByText('Модель')).toBeInTheDocument()
    expect(screen.getByText('Входные токены')).toBeInTheDocument()
    expect(screen.getByText('Выходные токены')).toBeInTheDocument()
    expect(screen.getByText('Всего токенов')).toBeInTheDocument()
    expect(screen.getByText('Стоимость ($)')).toBeInTheDocument()
  })

  it('allows filtering tokens by role', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    const devBadge = screen.getByText('Dev')
    fireEvent.click(devBadge)
    
    // Проверяем, что фильтр применился
    expect(devBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows filtering tokens by model', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    const qwenBadge = screen.getByText('qwen-plus')
    fireEvent.click(qwenBadge)
    
    // Проверяем, что фильтр применился
    expect(qwenBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows searching tokens', () => {
    render(
      <BrowserRouter>
        <Tokens />
      </BrowserRouter>
    )
    
    const searchInput = screen.getByPlaceholderText('Поиск по роли или модели...')
    fireEvent.change(searchInput, { target: { value: 'Architect' } })
    
    // Проверяем, что значение ввода изменилось
    expect(searchInput).toHaveValue('Architect')
  })
})