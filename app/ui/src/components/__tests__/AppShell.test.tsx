import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AppShell } from '@/components/AppShell'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/'
  })
}))

describe('AppShell', () => {
  it('renders app title', () => {
    render(
      <BrowserRouter>
        <AppShell>
          <div>Test content</div>
        </AppShell>
      </BrowserRouter>
    )
    
    expect(screen.getByText('Feature Factory')).toBeInTheDocument()
  })

  it('renders navigation items', () => {
    render(
      <BrowserRouter>
        <AppShell>
          <div>Test content</div>
        </AppShell>
      </BrowserRouter>
    )
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Features')).toBeInTheDocument()
    expect(screen.getByText('Tasks')).toBeInTheDocument()
    expect(screen.getByText('Runs')).toBeInTheDocument()
    expect(screen.getByText('Logs')).toBeInTheDocument()
    expect(screen.getByText('Tokens')).toBeInTheDocument()
    expect(screen.getByText('Docs')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Chat')).toBeInTheDocument()
  })

  it('renders environment badge', () => {
    render(
      <BrowserRouter>
        <AppShell>
          <div>Test content</div>
        </AppShell>
      </BrowserRouter>
    )
    
    expect(screen.getByText('TEST')).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(
      <BrowserRouter>
        <AppShell>
          <div data-testid="test-content">Test content</div>
        </AppShell>
      </BrowserRouter>
    )
    
    expect(screen.getByTestId('test-content')).toBeInTheDocument()
    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  it('highlights active navigation item', () => {
    render(
      <BrowserRouter>
        <AppShell>
          <div>Test content</div>
        </AppShell>
      </BrowserRouter>
    )
    
    const dashboardLink = screen.getByText('Dashboard').closest('a')
    expect(dashboardLink).toHaveClass('bg-blue-50')
  })

  it('renders mobile menu button', () => {
    render(
      <BrowserRouter>
        <AppShell>
          <div>Test content</div>
        </AppShell>
      </BrowserRouter>
    )
    
    // Проверяем, что кнопка меню существует (может быть скрыта на больших экранах)
    const menuButton = screen.getByRole('button', { name: 'Menu' })
    expect(menuButton).toBeInTheDocument()
  })

  it('renders close button in sidebar', () => {
    render(
      <BrowserRouter>
        <AppShell>
          <div>Test content</div>
        </AppShell>
      </BrowserRouter>
    )
    
    // Проверяем, что кнопка закрытия существует (может быть скрыта на больших экранах)
    const closeButton = screen.getByRole('button', { name: 'X' })
    expect(closeButton).toBeInTheDocument()
  })
})