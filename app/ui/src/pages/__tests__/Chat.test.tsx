import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Chat from '@/pages/Chat'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/chat'
  })
}))

// Мокаем setTimeout для ускорения тестов
jest.useFakeTimers()

describe('Chat', () => {
  it('renders chat title', () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Chat (Maintainer)')).toBeInTheDocument()
    expect(screen.getByText('Ввод на естественном языке → генерация интента и плана → создание фичи')).toBeInTheDocument()
  })

  it('renders clear chat button', () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Очистить чат' })).toBeInTheDocument()
  })

  it('renders empty chat state', () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Начните диалог')).toBeInTheDocument()
    expect(screen.getByText('Введите ваш запрос на естественном языке для генерации фичи')).toBeInTheDocument()
  })

  it('renders input area', () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    expect(screen.getByPlaceholderText('Опишите фичу на естественном языке...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument()
    expect(screen.getByText('Нажмите Enter для отправки, Shift+Enter для новой строки')).toBeInTheDocument()
  })

  it('allows sending a message', async () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова
    jest.advanceTimersByTime(1500)
    
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('shows generating intent state', async () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Проверяем, что появилось состояние генерации интента
    expect(screen.getByText('Генерация...')).toBeInTheDocument()
  })

  it('displays generated intent', async () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова
    jest.advanceTimersByTime(1500)
    
    // Проверяем, что отобразился сгенерированный интент
    expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    expect(screen.getByText('Новая фича из чата')).toBeInTheDocument()
  })

  it('allows generating plan from intent', async () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова
    jest.advanceTimersByTime(1500)
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова
    jest.advanceTimersByTime(2000)
    
    // Проверяем, что появилось состояние генерации плана
    expect(screen.getByText('Генерация плана...')).toBeInTheDocument()
  })

  it('displays generated plan', async () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова интента
    jest.advanceTimersByTime(1500)
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова плана
    jest.advanceTimersByTime(2000)
    
    // Проверяем, что отобразился сгенерированный план
    expect(screen.getByText('Сгенерированный план')).toBeInTheDocument()
    expect(screen.getByText('design_schema')).toBeInTheDocument()
    expect(screen.getByText('implement_feature')).toBeInTheDocument()
  })

  it('allows creating feature from intent', async () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова интента
    jest.advanceTimersByTime(1500)
    
    const createFeatureButton = screen.getByRole('button', { name: 'Создать фичу' })
    fireEvent.click(createFeatureButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова создания фичи
    jest.advanceTimersByTime(1000)
    
    // Проверяем, что отобразилось сообщение о создании фичи
    expect(screen.getByText('Фича создана')).toBeInTheDocument()
    expect(screen.getByText('Новая фича')).toBeInTheDocument()
  })

  it('allows executing plan', async () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова интента
    jest.advanceTimersByTime(1500)
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова плана
    jest.advanceTimersByTime(2000)
    
    const executePlanButton = screen.getByRole('button', { name: 'Выполнить план' })
    fireEvent.click(executePlanButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова выполнения плана
    jest.advanceTimersByTime(1000)
    
    // Проверяем, что отобразилось сообщение об успешном выполнении плана
    expect(screen.getByText('План выполнен успешно')).toBeInTheDocument()
  })

  it('handles intent generation error', async () => {
    // Мокаем Promise.reject для симуляции ошибки
    const originalPromise = global.Promise
    global.Promise = {
      ...originalPromise,
      resolve: originalPromise.resolve,
      reject: originalPromise.reject,
      all: originalPromise.all,
      race: originalPromise.race,
      allSettled: originalPromise.allSettled,
    } as any
    
    // Переопределяем resolve для симуляции ошибки
    global.Promise.resolve = jest.fn().mockImplementation((value) => {
      if (typeof value === 'function') {
        return originalPromise.resolve(value()).catch(() => {
          throw new Error('Test error')
        })
      }
      return originalPromise.resolve(value)
    })
    
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Продвигаем таймеры для завершения симуляции API вызова
    jest.advanceTimersByTime(1500)
    
    // Проверяем, что отобразилось сообщение об ошибке
    expect(screen.getByText('Ошибка при генерации интента')).toBeInTheDocument()
    
    // Восстанавливаем оригинальный Promise
    global.Promise = originalPromise
  })

  // Восстанавливаем реальные таймеры после тестов
  afterAll(() => {
    jest.useRealTimers()
  })
})