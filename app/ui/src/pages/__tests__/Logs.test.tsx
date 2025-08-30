import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Logs from '@/pages/Logs'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/logs'
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

describe('Logs', () => {
  it('renders logs title', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Logs')).toBeInTheDocument()
    expect(screen.getByText('Поток логов в реальном времени с фильтрацией')).toBeInTheDocument()
  })

  it('renders control buttons', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Пауза' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Очистить' })).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    expect(screen.getByPlaceholderText('Поиск по событию или содержимому лога...')).toBeInTheDocument()
  })

  it('renders component filter badges', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('orchestrator')).toBeInTheDocument()
    expect(screen.getByText('llm_router')).toBeInTheDocument()
    expect(screen.getByText('validator')).toBeInTheDocument()
    expect(screen.getByText('executor')).toBeInTheDocument()
    expect(screen.getByText('db')).toBeInTheDocument()
    expect(screen.getByText('api')).toBeInTheDocument()
  })

  it('renders level filter badges', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('DEBUG')).toBeInTheDocument()
    expect(screen.getByText('INFO')).toBeInTheDocument()
    expect(screen.getByText('WARNING')).toBeInTheDocument()
    expect(screen.getByText('ERROR')).toBeInTheDocument()
    expect(screen.getByText('CRITICAL')).toBeInTheDocument()
  })

  it('renders role filter badges', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('Architect')).toBeInTheDocument()
    expect(screen.getByText('Dev')).toBeInTheDocument()
    expect(screen.getByText('QA')).toBeInTheDocument()
    expect(screen.getByText('Scribe')).toBeInTheDocument()
    expect(screen.getByText('Maintainer')).toBeInTheDocument()
    expect(screen.getByText('Orchestrator')).toBeInTheDocument()
  })

  it('renders auto-scroll checkbox', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    expect(screen.getByLabelText('Автопрокрутка')).toBeInTheDocument()
  })

  it('renders logs table', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Время')).toBeInTheDocument()
    expect(screen.getByText('Уровень')).toBeInTheDocument()
    expect(screen.getByText('Компонент')).toBeInTheDocument()
    expect(screen.getByText('Роль')).toBeInTheDocument()
    expect(screen.getByText('Событие')).toBeInTheDocument()
    expect(screen.getByText('Содержимое')).toBeInTheDocument()
    expect(screen.getByText('Действия')).toBeInTheDocument()
  })

  it('allows filtering logs by component', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    const orchestratorBadge = screen.getByText('orchestrator')
    fireEvent.click(orchestratorBadge)
    
    // Проверяем, что фильтр применился
    expect(orchestratorBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows filtering logs by level', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    const infoBadge = screen.getByText('INFO')
    fireEvent.click(infoBadge)
    
    // Проверяем, что фильтр применился
    expect(infoBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows filtering logs by role', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    const devBadge = screen.getByText('Dev')
    fireEvent.click(devBadge)
    
    // Проверяем, что фильтр применился
    expect(devBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows searching logs', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    const searchInput = screen.getByPlaceholderText('Поиск по событию или содержимому лога...')
    fireEvent.change(searchInput, { target: { value: 'job_started' } })
    
    // Проверяем, что значение ввода изменилось
    expect(searchInput).toHaveValue('job_started')
  })

  it('allows toggling auto-scroll', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    const autoScrollCheckbox = screen.getByLabelText('Автопрокрутка')
    fireEvent.click(autoScrollCheckbox)
    
    // Проверяем, что чекбокс изменил состояние
    expect(autoScrollCheckbox).not.toBeChecked()
  })

  it('allows toggling streaming', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    const pauseButton = screen.getByRole('button', { name: 'Пауза' })
    fireEvent.click(pauseButton)
    
    // После клика кнопка должна измениться на "Продолжить"
    expect(screen.getByRole('button', { name: 'Продолжить' })).toBeInTheDocument()
  })

  it('allows clearing logs', () => {
    render(
      <BrowserRouter>
        <Logs />
      </BrowserRouter>
    )
    
    const clearButton = screen.getByRole('button', { name: 'Очистить' })
    fireEvent.click(clearButton)
    
    // Проверяем, что появилось сообщение об отсутствии логов
    expect(screen.getByText('Логи не найдены')).toBeInTheDocument()
  })
})