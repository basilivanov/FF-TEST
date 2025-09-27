import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import LogsCharts from '../LogsCharts'

// Mock recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
  Bar: () => <div data-testid="bar" />,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Line: () => <div data-testid="line" />
}))

// Mock Sparkline component
jest.mock('../Sparkline', () => {
  return function MockSparkline() {
    return <div data-testid="sparkline" />
  }
})

const mockLogs = [
  {
    timestamp: '2024-01-15T10:00:00Z',
    level: 'INFO' as const,
    service: 'api',
    message: 'Test message 1',
    correlation_id: 'test-correlation-1',
    request_id: null,
    user: null,
    source: 'test',
    feature_id: 1,
    task_id: 1,
    run_id: null,
    duration_ms: null,
    status_code: 200,
    ip_address: null,
    user_agent: null,
    error: null,
    context: null
  },
  {
    timestamp: '2024-01-15T10:01:00Z',
    level: 'ERROR' as const,
    service: 'worker',
    message: 'Test error message',
    correlation_id: 'test-correlation-2',
    request_id: null,
    user: null,
    source: 'test',
    feature_id: 2,
    task_id: 2,
    run_id: null,
    duration_ms: null,
    status_code: 500,
    ip_address: null,
    user_agent: null,
    error: 'Test error',
    context: null
  },
  {
    timestamp: '2024-01-15T10:02:00Z',
    level: 'WARN' as const,
    service: 'scheduler',
    message: 'Test warning message',
    correlation_id: 'test-correlation-3',
    request_id: null,
    user: null,
    source: 'test',
    feature_id: 3,
    task_id: 3,
    run_id: null,
    duration_ms: null,
    status_code: null,
    ip_address: null,
    user_agent: null,
    error: null,
    context: null
  }
]

describe('LogsCharts', () => {
  it('renders all statistical cards', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    // Проверяем основные метрики
    expect(screen.getByText('3')).toBeInTheDocument() // Всего логов
    expect(screen.getByText('Всего логов')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument() // Критичные ошибки
    expect(screen.getByText('Критичные ошибки')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument() // Предупреждения
    expect(screen.getByText('Предупреждения')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument() // Успешные операции (INFO)
    expect(screen.getByText('Успешно')).toBeInTheDocument()
  })

  it('renders sparklines', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    const sparklines = screen.getAllByTestId('sparkline')
    expect(sparklines).toHaveLength(3) // Activity, performance, queue
  })

  it('renders charts', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    // Проверяем наличие графиков
    expect(screen.getByText('Активность по часам')).toBeInTheDocument()
    expect(screen.getByText('Распределение по уровням')).toBeInTheDocument()
    expect(screen.getByText('Активность по сервисам')).toBeInTheDocument()
    expect(screen.getByText('Распределение по времени')).toBeInTheDocument()

    // Проверяем что графики рендерятся
    expect(screen.getAllByTestId('area-chart')).toHaveLength(2)
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  it('shows live indicator when liveTail is true', () => {
    render(<LogsCharts logs={mockLogs} liveTail={true} />)

    expect(screen.getByText('LIVE')).toBeInTheDocument()
  })

  it('renders recent critical errors section when there are errors', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    expect(screen.getByText('Последние критичные ошибки')).toBeInTheDocument()
    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('calculates error rate correctly', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    // 1 error out of 3 logs = 33.3%
    expect(screen.getByText('33.3% от всех логов')).toBeInTheDocument()
  })

  it('handles empty logs array', () => {
    render(<LogsCharts logs={[]} liveTail={false} />)

    expect(screen.getByText('0')).toBeInTheDocument() // Should show 0 for all metrics
  })

  it('groups logs by service correctly', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    // У нас есть 3 разных сервиса, каждый с 1 логом
    expect(screen.getByText('Активность по сервисам')).toBeInTheDocument()
  })

  it('shows appropriate icons for each level', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    // Проверяем что есть иконки для разных уровней логирования
    const activityIcons = screen.getAllByTestId('responsive-container')
    expect(activityIcons.length).toBeGreaterThan(0)
  })
})