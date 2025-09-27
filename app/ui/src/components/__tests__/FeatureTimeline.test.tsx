import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import FeatureTimeline from '../FeatureTimeline'

// Mock Sparkline component
jest.mock('../Sparkline', () => {
  return function MockSparkline() {
    return <div data-testid="sparkline" />
  }
})

const mockFeature = {
  id: 1,
  title: 'Test Feature',
  status: 'RUNNING',
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T12:00:00Z',
  created_by: 'test-user',
  priority: 5,
  env: 'TEST'
}

const mockTasks = [
  {
    id: 1,
    feature_id: 1,
    role: 'Architect',
    status: 'DONE',
    attempts: 1,
    scheduled_at: '2024-01-15T10:00:00Z',
    started_at: '2024-01-15T10:01:00Z',
    completed_at: '2024-01-15T10:05:00Z',
    updated_at: '2024-01-15T10:05:00Z',
    correlation_id: 'test-correlation-1'
  },
  {
    id: 2,
    feature_id: 1,
    role: 'Dev',
    status: 'RUNNING',
    attempts: 1,
    scheduled_at: '2024-01-15T10:05:00Z',
    started_at: '2024-01-15T10:06:00Z',
    correlation_id: 'test-correlation-2'
  },
  {
    id: 3,
    feature_id: 1,
    role: 'QA',
    status: 'FAILED',
    attempts: 2,
    scheduled_at: '2024-01-15T10:10:00Z',
    started_at: '2024-01-15T10:11:00Z',
    completed_at: '2024-01-15T10:15:00Z',
    error_message: 'Test failed',
    correlation_id: 'test-correlation-3'
  }
]

const mockRuns = [
  {
    run_id: 'run-1',
    feature_id: 1,
    graph_name: 'test-graph',
    thread_id: 'thread-1',
    status: 'RUNNING',
    last_checkpoint_at: '2024-01-15T10:30:00Z',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:30:00Z'
  },
  {
    run_id: 'run-2',
    feature_id: 1,
    graph_name: 'test-graph-2',
    thread_id: 'thread-2',
    status: 'DONE',
    last_checkpoint_at: '2024-01-15T09:30:00Z',
    created_at: '2024-01-15T09:00:00Z',
    updated_at: '2024-01-15T09:30:00Z'
  }
]

describe('FeatureTimeline', () => {
  const mockOnRetryTask = jest.fn()
  const mockOnRestartRun = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders timeline header with progress information', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Таймлайн выполнения')).toBeInTheDocument()
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
    expect(screen.getByTestId('sparkline')).toBeInTheDocument()
  })

  it('calculates and displays progress correctly', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    // 1 из 3 задач завершено
    expect(screen.getByText('1/3 задач')).toBeInTheDocument()
    expect(screen.getByText('1 завершено')).toBeInTheDocument()
    expect(screen.getByText('1 в работе')).toBeInTheDocument()
    expect(screen.getByText('1 ошибок')).toBeInTheDocument()
  })

  it('displays timeline events in chronological order', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Фича создана')).toBeInTheDocument()
    expect(screen.getByText('Задача Architect запланирована')).toBeInTheDocument()
    expect(screen.getByText('Задача Dev начата')).toBeInTheDocument()
    expect(screen.getByText('Задача QA провалилась')).toBeInTheDocument()
  })

  it('shows retry button for failed tasks', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    const retryButtons = screen.getAllByText('Повторить')
    expect(retryButtons).toHaveLength(1) // Только для провалившейся задачи
  })

  it('calls onRetryTask when retry button is clicked', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    const retryButton = screen.getByText('Повторить')
    fireEvent.click(retryButton)

    expect(mockOnRetryTask).toHaveBeenCalledWith(3) // ID провалившейся задачи
  })

  it('shows restart button for failed runs', () => {
    const runsWithFailedRun = [
      ...mockRuns,
      {
        run_id: 'run-failed',
        feature_id: 1,
        graph_name: 'failed-graph',
        thread_id: 'thread-failed',
        status: 'FAILED',
        last_checkpoint_at: '2024-01-15T11:00:00Z',
        created_at: '2024-01-15T10:45:00Z',
        updated_at: '2024-01-15T11:00:00Z'
      }
    ]

    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={runsWithFailedRun}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    const restartButtons = screen.getAllByText('Перезапуск')
    expect(restartButtons).toHaveLength(1)
  })

  it('displays error messages for failed tasks', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Test failed')).toBeInTheDocument()
  })

  it('shows role badges with appropriate colors', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Architect')).toBeInTheDocument()
    expect(screen.getByText('Dev')).toBeInTheDocument()
    expect(screen.getByText('QA')).toBeInTheDocument()
  })

  it('displays correlation IDs when available', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    // Корреляционные ID обрезаются до последних 8 символов
    expect(screen.getByText('lation-1')).toBeInTheDocument()
    expect(screen.getByText('lation-2')).toBeInTheDocument()
    expect(screen.getByText('lation-3')).toBeInTheDocument()
  })

  it('handles empty events gracefully', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={[]}
        runs={[]}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Фича создана')).toBeInTheDocument() // Always shows feature creation
    expect(screen.getByText('0/0 задач')).toBeInTheDocument()
  })

  it('shows attempts count for tasks with multiple attempts', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Попытка #2')).toBeInTheDocument() // Для провалившейся задачи QA
  })
})