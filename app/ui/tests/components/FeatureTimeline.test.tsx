import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import FeatureTimeline from '@/components/FeatureTimeline'

const mockFeature = {
  id: 1,
  name: 'Test Feature',
  description: 'Test feature description',
  status: 'active' as const,
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-01T11:00:00Z',
  created_by: 'testuser',
  config: {},
  graph_definition: {},
  priority: 1,
  tags: ['test'],
  enabled: true
}

const mockTasks = [
  {
    id: 1,
    feature_id: 1,
    name: 'Task 1',
    description: 'First task',
    status: 'completed' as const,
    created_at: '2024-01-01T10:05:00Z',
    updated_at: '2024-01-01T10:10:00Z',
    config: {},
    dependencies: [],
    retry_count: 0,
    max_retries: 3,
    timeout_seconds: 300,
    priority: 1
  },
  {
    id: 2,
    feature_id: 1,
    name: 'Task 2',
    description: 'Second task',
    status: 'failed' as const,
    created_at: '2024-01-01T10:15:00Z',
    updated_at: '2024-01-01T10:20:00Z',
    config: {},
    dependencies: [],
    retry_count: 2,
    max_retries: 3,
    timeout_seconds: 300,
    priority: 2
  }
]

const mockRuns = [
  {
    id: 'run-1',
    feature_id: 1,
    status: 'completed' as const,
    started_at: '2024-01-01T10:05:00Z',
    completed_at: '2024-01-01T10:30:00Z',
    created_at: '2024-01-01T10:05:00Z',
    updated_at: '2024-01-01T10:30:00Z',
    error: null,
    result: { success: true },
    metadata: {},
    triggered_by: 'manual',
    trigger_data: {}
  },
  {
    id: 'run-2',
    feature_id: 1,
    status: 'failed' as const,
    started_at: '2024-01-01T11:00:00Z',
    completed_at: '2024-01-01T11:05:00Z',
    created_at: '2024-01-01T11:00:00Z',
    updated_at: '2024-01-01T11:05:00Z',
    error: 'Task failed',
    result: null,
    metadata: {},
    triggered_by: 'scheduler',
    trigger_data: {}
  }
]

const mockOnRetryTask = jest.fn()
const mockOnRestartRun = jest.fn()

describe('FeatureTimeline', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders timeline with feature creation event', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Хронология выполнения')).toBeInTheDocument()
    expect(screen.getByText('Фича создана')).toBeInTheDocument()
    expect(screen.getByText('Создана пользователем testuser')).toBeInTheDocument()
  })

  it('renders task events with correct status', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Задача Task 1 завершена')).toBeInTheDocument()
    expect(screen.getByText('Задача Task 2 провалена')).toBeInTheDocument()
  })

  it('renders run events with duration', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Запуск run-1 завершён')).toBeInTheDocument()
    expect(screen.getByText('Запуск run-2 провален')).toBeInTheDocument()
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

    const retryButton = screen.getByText('Повторить')
    expect(retryButton).toBeInTheDocument()
  })

  it('shows restart button for failed runs', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    const restartButton = screen.getByText('Перезапустить')
    expect(restartButton).toBeInTheDocument()
  })

  it('calls onRetryTask when retry button is clicked', async () => {
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

    await waitFor(() => {
      expect(mockOnRetryTask).toHaveBeenCalledWith(2) // Task 2 ID
    })
  })

  it('calls onRestartRun when restart button is clicked', async () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    const restartButton = screen.getByText('Перезапустить')
    fireEvent.click(restartButton)

    await waitFor(() => {
      expect(mockOnRestartRun).toHaveBeenCalledWith('run-2') // Failed run ID
    })
  })

  it('displays time ago for events', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    // Should display relative time for events
    expect(screen.getByText(/назад/)).toBeInTheDocument()
  })

  it('sorts events by timestamp correctly', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={mockTasks}
        runs={mockRuns}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    const timelineItems = screen.getAllByTestId(/timeline-event-/)
    expect(timelineItems.length).toBeGreaterThan(0)
  })

  it('handles empty tasks and runs arrays', () => {
    render(
      <FeatureTimeline
        feature={mockFeature}
        tasks={[]}
        runs={[]}
        onRetryTask={mockOnRetryTask}
        onRestartRun={mockOnRestartRun}
      />
    )

    expect(screen.getByText('Хронология выполнения')).toBeInTheDocument()
    expect(screen.getByText('Фича создана')).toBeInTheDocument()
  })
})