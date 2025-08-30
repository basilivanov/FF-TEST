import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { routes } from '@/routes'

describe('Routes', () => {
  it('renders Dashboard component for / route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Обзор состояния системы Feature Factory')).toBeInTheDocument()
  })

  it('renders Features component for /features route', () => {
    render(
      <MemoryRouter initialEntries={['/features']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Features')).toBeInTheDocument()
    expect(screen.getByText('Управление фичами и их жизненным циклом')).toBeInTheDocument()
  })

  it('renders FeatureDetail component for /features/:id route', () => {
    render(
      <MemoryRouter initialEntries={['/features/1']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('ETL Pipeline Implementation')).toBeInTheDocument()
    expect(screen.getByText('Детали фичи и управление её выполнением')).toBeInTheDocument()
  })

  it('renders Tasks component for /tasks route', () => {
    render(
      <MemoryRouter initialEntries={['/tasks']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Tasks')).toBeInTheDocument()
    expect(screen.getByText('Управление задачами и их выполнением')).toBeInTheDocument()
  })

  it('renders Runs component for /runs route', () => {
    render(
      <MemoryRouter initialEntries={['/runs']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Runs')).toBeInTheDocument()
    expect(screen.getByText('Управление запусками графов и их состоянием')).toBeInTheDocument()
  })

  it('renders Logs component for /logs route', () => {
    render(
      <MemoryRouter initialEntries={['/logs']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Logs')).toBeInTheDocument()
    expect(screen.getByText('Поток логов в реальном времени с фильтрацией')).toBeInTheDocument()
  })

  it('renders Tokens component for /tokens route', () => {
    render(
      <MemoryRouter initialEntries={['/tokens']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Tokens')).toBeInTheDocument()
    expect(screen.getByText('Сводка расхода токенов по ролям и моделям')).toBeInTheDocument()
  })

  it('renders Docs component for /docs route', () => {
    render(
      <MemoryRouter initialEntries={['/docs']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Docs')).toBeInTheDocument()
    expect(screen.getByText('Управление документацией и ее актуальность')).toBeInTheDocument()
  })

  it('renders Settings component for /settings route', () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Настройки системы (только чтение в MVP)')).toBeInTheDocument()
  })

  it('renders Chat component for /chat route', () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        {routes}
      </MemoryRouter>
    )
    
    expect(screen.getByText('Chat (Maintainer)')).toBeInTheDocument()
    expect(screen.getByText('Ввод на естественном языке → генерация интента и плана → создание фичи')).toBeInTheDocument()
  })
})