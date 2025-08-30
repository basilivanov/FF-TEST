import React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '@/pages/Dashboard'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/'
  })
}))

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Обзор состояния системы Feature Factory')).toBeInTheDocument()
  })

  it('renders environment banner', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Тестовое окружение')).toBeInTheDocument()
    expect(screen.getByText('все данные являются демо-данными')).toBeInTheDocument()
  })

  it('renders dashboard cards', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )
    
    expect(screen.getByText('System Health')).toBeInTheDocument()
    expect(screen.getByText('Backlog')).toBeInTheDocument()
    expect(screen.getByText('Recent Runs')).toBeInTheDocument()
    expect(screen.getByText('LLM Budgets')).toBeInTheDocument()
    expect(screen.getByText('Recent Errors')).toBeInTheDocument()
    expect(screen.getByText('Docs')).toBeInTheDocument()
  })

  it('renders refresh button', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Refresh Data' })).toBeInTheDocument()
  })
})