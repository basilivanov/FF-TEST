import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Settings from '@/pages/Settings'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/settings'
  })
}))

// Мокаем console.log для проверки вызовов
console.log = jest.fn()

describe('Settings', () => {
  it('renders settings title', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Настройки системы (только чтение в MVP)')).toBeInTheDocument()
  })

  it('renders action buttons', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Редактировать' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Сбросить' })).toBeInTheDocument()
  })

  it('renders timezone setting', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Часовой пояс приложения')).toBeInTheDocument()
    expect(screen.getByLabelText('APP_TZ')).toBeInTheDocument()
    expect(screen.getByText('Текущее время:')).toBeInTheDocument()
  })

  it('renders schedules section', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Расписания')).toBeInTheDocument()
    expect(screen.getByLabelText('ETL Daily')).toBeInTheDocument()
    expect(screen.getByLabelText('Backup Weekly')).toBeInTheDocument()
    expect(screen.getByLabelText('Cleanup Monthly')).toBeInTheDocument()
  })

  it('renders API keys section', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    expect(screen.getByText('API Keys')).toBeInTheDocument()
    expect(screen.getByLabelText('OpenAI')).toBeInTheDocument()
    expect(screen.getByLabelText('Anthropic')).toBeInTheDocument()
    expect(screen.getByLabelText('Gemini')).toBeInTheDocument()
  })

  it('renders IDs section', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Идентификаторы')).toBeInTheDocument()
    expect(screen.getByLabelText('Project ID')).toBeInTheDocument()
    expect(screen.getByLabelText('Cluster ID')).toBeInTheDocument()
    expect(screen.getByLabelText('Region')).toBeInTheDocument()
  })

  it('allows editing settings', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    const editButton = screen.getByRole('button', { name: 'Редактировать' })
    fireEvent.click(editButton)
    
    // Проверяем, что поля ввода стали доступны для редактирования
    const appTzInput = screen.getByLabelText('APP_TZ')
    expect(appTzInput).not.toHaveClass('bg-gray-50')
    
    // Проверяем, что появились кнопки сохранения и отмены
    expect(screen.getByRole('button', { name: 'Отменить' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Сохранить изменения' })).toBeInTheDocument()
  })

  it('allows changing timezone setting', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    const editButton = screen.getByRole('button', { name: 'Редактировать' })
    fireEvent.click(editButton)
    
    const appTzInput = screen.getByLabelText('APP_TZ')
    fireEvent.change(appTzInput, { target: { value: 'America/New_York' } })
    
    // Проверяем, что значение изменилось
    expect(appTzInput).toHaveValue('America/New_York')
  })

  it('allows resetting settings', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    const resetButton = screen.getByRole('button', { name: 'Сбросить' })
    fireEvent.click(resetButton)
    
    // Проверяем, что функция сброса была вызвана
    expect(console.log).toHaveBeenCalledWith('Resetting settings to default')
  })

  it('allows saving settings', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    const editButton = screen.getByRole('button', { name: 'Редактировать' })
    fireEvent.click(editButton)
    
    const saveButton = screen.getByRole('button', { name: 'Сохранить изменения' })
    fireEvent.click(saveButton)
    
    // Проверяем, что функция сохранения была вызвана
    expect(console.log).toHaveBeenCalledWith('Saving settings:', expect.any(Object))
  })

  it('allows canceling editing', () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )
    
    const editButton = screen.getByRole('button', { name: 'Редактировать' })
    fireEvent.click(editButton)
    
    const cancelButton = screen.getByRole('button', { name: 'Отменить' })
    fireEvent.click(cancelButton)
    
    // Проверяем, что кнопки сохранения и отмены исчезли
    expect(screen.queryByRole('button', { name: 'Отменить' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Сохранить изменения' })).not.toBeInTheDocument()
  })
})