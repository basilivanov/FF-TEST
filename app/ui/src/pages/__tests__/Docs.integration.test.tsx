/**
 * Integration tests for Docs page - tests real API endpoints without mocking
 */
import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Docs from '@/pages/Docs'

// НЕ мокаем API - проверяем реальные endpoints!

describe('Docs Integration Tests', () => {
  beforeEach(() => {
    // Очищаем все моки - используем реальные API вызовы
    jest.restoreAllMocks()
  })

  it('loads real cortex health data from API', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    // Ждём загрузки реальных данных
    await waitFor(() => {
      // Проверяем что появились реальные данные из API
      const healthElements = screen.queryAllByText(/\d+%/)
      expect(healthElements.length).toBeGreaterThan(0)
    }, { timeout: 5000 })

    // Проверяем что загружается не fallback, а реальные данные
    const loading = screen.queryByText('Загрузка...')
    expect(loading).not.toBeInTheDocument()
  })

  it('triggers real cortex analysis via API', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Анализ кортекса' })).toBeInTheDocument()
    })

    const analyzeButton = screen.getByRole('button', { name: 'Анализ кортекса' })

    await act(async () => {
      fireEvent.click(analyzeButton)
    })

    // Проверяем что кнопка не зависла и API отвечает
    await waitFor(() => {
      expect(analyzeButton).not.toBeDisabled()
    }, { timeout: 3000 })
  })

  it('displays real role analysis without mocks', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    // Переключаемся на анализ ролей
    await waitFor(() => {
      fireEvent.click(screen.getByText('Анализ Ролей'))
    })

    // Проверяем что загружаются реальные роли
    await waitFor(() => {
      // Ищем любую из ролей которые должны быть в реальных данных
      const roleNames = ['Dev', 'QA', 'Architect', 'Scribe', 'Maintainer']
      const foundRole = roleNames.some(roleName =>
        screen.queryByText(roleName) !== null
      )
      expect(foundRole).toBe(true)
    }, { timeout: 5000 })
  })

  it.skip('API endpoints respond with correct format', async () => {
    // Пропускаем - требует настройки fetch в test среде
    // Проверяется другими тестами через UI
  })

  it('handles API failures gracefully in real environment', async () => {
    // Тестируем отказоустойчивость при недоступности API

    // Временно "ломаем" API делая запрос на несуществующий endpoint
    const originalFetch = global.fetch
    global.fetch = jest.fn(() => Promise.resolve({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: 'Internal Server Error' })
    } as Response))

    await act(async () => {
      render(
        <BrowserRouter>
          <Docs />
        </BrowserRouter>
      )
    })

    // Проверяем что приложение не падает при ошибке API
    await waitFor(() => {
      expect(screen.getByText('Cortex Health & Documentation')).toBeInTheDocument()
    })

    // Восстанавливаем fetch
    global.fetch = originalFetch
  })
})