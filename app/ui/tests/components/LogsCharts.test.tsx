import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import LogsCharts from '@/components/LogsCharts'

const mockLogs = [
  {
    timestamp: '2024-01-01T10:00:00Z',
    level: 'INFO' as const,
    service: 'api',
    message: 'Test info message',
    correlation_id: 'test-123',
    request_id: 'req-123',
    user: 'testuser',
    source: 'api.log',
    feature_id: 1,
    task_id: 1,
    run_id: 'run-123',
    duration_ms: 100,
    status_code: 200,
    ip_address: '127.0.0.1',
    user_agent: 'test-agent',
    error: null,
    context: {}
  },
  {
    timestamp: '2024-01-01T10:01:00Z',
    level: 'ERROR' as const,
    service: 'worker',
    message: 'Test error message',
    correlation_id: 'test-456',
    request_id: 'req-456',
    user: 'testuser',
    source: 'worker.log',
    feature_id: 2,
    task_id: 2,
    run_id: 'run-456',
    duration_ms: 500,
    status_code: 500,
    ip_address: '127.0.0.1',
    user_agent: 'test-agent',
    error: 'Test error',
    context: {}
  },
  {
    timestamp: '2024-01-01T10:02:00Z',
    level: 'WARN' as const,
    service: 'scheduler',
    message: 'Test warning message',
    correlation_id: 'test-789',
    request_id: 'req-789',
    user: 'testuser',
    source: 'scheduler.log',
    feature_id: 3,
    task_id: 3,
    run_id: 'run-789',
    duration_ms: 200,
    status_code: 400,
    ip_address: '127.0.0.1',
    user_agent: 'test-agent',
    error: null,
    context: {}
  }
]

describe('LogsCharts', () => {
  it('renders logs overview cards', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    expect(screen.getByText('Обзор логов')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument() // Total logs count
  })

  it('renders level distribution chart', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    expect(screen.getByText('Распределение по уровням')).toBeInTheDocument()
  })

  it('renders service activity chart', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    expect(screen.getByText('Активность сервисов')).toBeInTheDocument()
  })

  it('renders time distribution chart', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    expect(screen.getByText('Распределение по времени')).toBeInTheDocument()
  })

  it('shows live tail indicator when active', () => {
    render(<LogsCharts logs={mockLogs} liveTail={true} />)

    const liveTailIndicator = screen.getByText('Live Tail')
    expect(liveTailIndicator).toBeInTheDocument()
  })

  it('calculates statistics correctly', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    // Check for error rate calculation
    const errorRate = ((1 / 3) * 100).toFixed(1) + '%' // 1 error out of 3 logs
    expect(screen.getByText(errorRate)).toBeInTheDocument()
  })

  it('handles empty logs array', () => {
    render(<LogsCharts logs={[]} liveTail={false} />)

    expect(screen.getByText('Обзор логов')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('renders sparklines in statistics cards', () => {
    render(<LogsCharts logs={mockLogs} liveTail={false} />)

    // Sparklines should be present in stats cards
    const sparklineContainers = screen.getAllByTestId(/sparkline/)
    expect(sparklineContainers.length).toBeGreaterThan(0)
  })
})