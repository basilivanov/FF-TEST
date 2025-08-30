import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Docs from '@/pages/Docs'

// Мокаем useLocation hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/docs'
  })
}))

describe('Docs', () => {
  it('renders docs title', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Docs')).toBeInTheDocument()
    expect(screen.getByText('Управление документацией и ее актуальность')).toBeInTheDocument()
  })

  it('renders rebuild documentation button', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: 'Пересобрать документацию' })).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    expect(screen.getByPlaceholderText('Поиск по названию документа или версии...')).toBeInTheDocument()
  })

  it('renders status filter badges', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Все')).toBeInTheDocument()
    expect(screen.getByText('Up to date')).toBeInTheDocument()
    expect(screen.getByText('Outdated')).toBeInTheDocument()
    expect(screen.getByText('Draft')).toBeInTheDocument()
  })

  it('renders docs summary', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Сводка документации')).toBeInTheDocument()
    expect(screen.getByText('Всего документов:')).toBeInTheDocument()
    expect(screen.getByText('Актуальные')).toBeInTheDocument()
    expect(screen.getByText('Устаревшие')).toBeInTheDocument()
    expect(screen.getByText('Черновики')).toBeInTheDocument()
  })

  it('renders documents table', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Название документа')).toBeInTheDocument()
    expect(screen.getByText('Версия')).toBeInTheDocument()
    expect(screen.getByText('Хэш содержимого')).toBeInTheDocument()
    expect(screen.getByText('Обновлено')).toBeInTheDocument()
    expect(screen.getByText('Статус')).toBeInTheDocument()
    expect(screen.getByText('Действия')).toBeInTheDocument()
  })

  it('allows filtering docs by status', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    const draftBadge = screen.getByText('Draft')
    fireEvent.click(draftBadge)
    
    // Проверяем, что фильтр применился
    expect(draftBadge).toHaveClass('bg-blue-500') // Проверяем, что бейдж стал активным
  })

  it('allows searching docs', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    const searchInput = screen.getByPlaceholderText('Поиск по названию документа или версии...')
    fireEvent.change(searchInput, { target: { value: 'Architecture' } })
    
    // Проверяем, что значение ввода изменилось
    expect(searchInput).toHaveValue('Architecture')
  })

  it('allows rebuilding documentation', () => {
    render(
      <BrowserRouter>
        <Docs />
      </BrowserRouter>
    )
    
    const rebuildButton = screen.getByRole('button', { name: 'Пересобрать документацию' })
    fireEvent.click(rebuildButton)
    
    // Проверяем, что функция пересборки была вызвана (через console.log в моке)
    expect(console.log).toHaveBeenCalledWith('Rebuilding documentation...')
  })
})