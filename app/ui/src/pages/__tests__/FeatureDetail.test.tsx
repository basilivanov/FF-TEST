import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import FeatureDetail from '@/pages/FeatureDetail'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/features/1'
  }),
  useParams: () => ({
    id: '1'
  })
}))

describe('FeatureDetail', () => {
  it('renders feature detail title', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    expect(screen.getByText('ETL Pipeline Implementation')).toBeInTheDocument()
    expect(screen.getByText('Детали фичи и управление её выполнением')).toBeInTheDocument()
  })

  it('renders back link', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    expect(screen.getByText('Назад к списку фич')).toBeInTheDocument()
  })

  it('renders action buttons', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Запустить' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Редактировать' })).toBeInTheDocument()
  })

  it('renders feature overview', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    expect(screen.getByText('Описание фичи')).toBeInTheDocument()
    expect(screen.getByText('Create a robust ETL pipeline for processing incoming data from various sources')).toBeInTheDocument()
  })

  it('renders status card', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    expect(screen.getByText('Статус')).toBeInTheDocument()
    expect(screen.getByText('Выполняется')).toBeInTheDocument()
    expect(screen.getByText('Приоритет')).toBeInTheDocument()
    expect(screen.getByText('Environment')).toBeInTheDocument()
    expect(screen.getByText('test')).toBeInTheDocument()
  })

  it('renders metadata card', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    expect(screen.getByText('Метаданные')).toBeInTheDocument()
    expect(screen.getByText('Автор:')).toBeInTheDocument()
    expect(screen.getByText('admin')).toBeInTheDocument()
    expect(screen.getByText('Создано:')).toBeInTheDocument()
    expect(screen.getByText('ID:')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('renders tabs', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    expect(screen.getByText('Задачи (3)')).toBeInTheDocument()
    expect(screen.getByText('История запусков (2)')).toBeInTheDocument()
  })

  it('renders tasks table by default', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    expect(screen.getByText('Задача')).toBeInTheDocument()
    expect(screen.getByText('Роль')).toBeInTheDocument()
    expect(screen.getByText('Статус')).toBeInTheDocument()
    expect(screen.getByText('Попытки')).toBeInTheDocument()
    expect(screen.getByText('Бюджет токенов')).toBeInTheDocument()
    expect(screen.getByText('Расписание')).toBeInTheDocument()
    expect(screen.getByText('Действия')).toBeInTheDocument()
    
    // Проверяем, что отображаются задачи
    expect(screen.getByText('Задача #1')).toBeInTheDocument()
    expect(screen.getByText('Задача #2')).toBeInTheDocument()
    expect(screen.getByText('Задача #3')).toBeInTheDocument()
  })

  it('switches to run history tab', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    const historyTab = screen.getByText('История запусков (2)')
    fireEvent.click(historyTab)
    
    // Проверяем, что отображается таблица истории запусков
    expect(screen.getByText('ID запуска')).toBeInTheDocument()
    expect(screen.getByText('Начало')).toBeInTheDocument()
    expect(screen.getByText('Завершение')).toBeInTheDocument()
    expect(screen.getByText('Статус')).toBeInTheDocument()
    expect(screen.getByText('Инициатор')).toBeInTheDocument()
    
    // Проверяем, что отображаются записи истории
    expect(screen.getByText('run-001')).toBeInTheDocument()
    expect(screen.getByText('run-002')).toBeInTheDocument()
  })

  it('switches back to tasks tab', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        <FeatureDetail />
      </MemoryRouter>
    )
    
    // Сначала переключаемся на историю
    const historyTab = screen.getByText('История запусков (2)')
    fireEvent.click(historyTab)
    
    // Затем переключаемся обратно на задачи
    const tasksTab = screen.getByText('Задачи (3)')
    fireEvent.click(tasksTab)
    
    // Проверяем, что снова отображается таблица задач
    expect(screen.getByText('Задача')).toBeInTheDocument()
    expect(screen.getByText('Роль')).toBeInTheDocument()
    expect(screen.getByText('Статус')).toBeInTheDocument()
  })
})