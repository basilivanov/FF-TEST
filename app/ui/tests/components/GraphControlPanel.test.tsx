import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import GraphControlPanel from '@/components/GraphControlPanel'

// Mock the API utilities
jest.mock('@/lib/api', () => ({
  post: jest.fn(),
}))

const { post } = require('@/lib/api')

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
    status: 'running' as const,
    started_at: '2024-01-01T11:00:00Z',
    completed_at: null,
    created_at: '2024-01-01T11:00:00Z',
    updated_at: '2024-01-01T11:05:00Z',
    error: null,
    result: null,
    metadata: {},
    triggered_by: 'scheduler',
    trigger_data: {}
  }
]

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
  }
]

const mockOnRefresh = jest.fn()

describe('GraphControlPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    post.mockResolvedValue({})
  })

  it('renders control panel with feature information', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Управление графом')).toBeInTheDocument()
    expect(screen.getByText('Test Feature')).toBeInTheDocument()
  })

  it('displays run metrics correctly', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Общие запуски')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument() // Total runs
    expect(screen.getByText('Активные запуски')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument() // Active runs
  })

  it('displays task metrics correctly', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Общие задачи')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument() // Total tasks
  })

  it('shows success rate calculation', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Успешность')).toBeInTheDocument()
    // Should show success rate based on completed runs
  })

  it('renders run feature button', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const runButton = screen.getByText('Запустить фичу')
    expect(runButton).toBeInTheDocument()
  })

  it('renders stop feature button when feature is running', () => {
    const runningRuns = [
      {
        ...mockRuns[0],
        status: 'running' as const,
        completed_at: null
      }
    ]

    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={runningRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const stopButton = screen.getByText('Остановить выполнение')
    expect(stopButton).toBeInTheDocument()
  })

  it('renders tick timer button', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const tickButton = screen.getByText('Tick таймер')
    expect(tickButton).toBeInTheDocument()
  })

  it('calls API when run feature button is clicked', async () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const runButton = screen.getByText('Запустить фичу')
    fireEvent.click(runButton)

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/orchestrator/features/1/run')
      expect(mockOnRefresh).toHaveBeenCalled()
    })
  })

  it('calls API when stop feature button is clicked', async () => {
    const runningRuns = [
      {
        ...mockRuns[0],
        status: 'running' as const,
        completed_at: null
      }
    ]

    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={runningRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const stopButton = screen.getByText('Остановить выполнение')
    fireEvent.click(stopButton)

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/orchestrator/features/1/stop')
      expect(mockOnRefresh).toHaveBeenCalled()
    })
  })

  it('calls API when tick timer button is clicked', async () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const tickButton = screen.getByText('Tick таймер')
    fireEvent.click(tickButton)

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/orchestrator/runner/tick')
      expect(mockOnRefresh).toHaveBeenCalled()
    })
  })

  it('shows loading state during API calls', async () => {
    // Make post return a promise that doesn't resolve immediately
    post.mockReturnValue(new Promise(resolve => setTimeout(resolve, 100)))

    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const runButton = screen.getByText('Запустить фичу')
    fireEvent.click(runButton)

    // Button should show loading state
    expect(runButton).toBeDisabled()
  })

  it('enables auto-refresh toggle', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const autoRefreshToggle = screen.getByLabelText('Авто-обновление')
    expect(autoRefreshToggle).toBeInTheDocument()
    expect(autoRefreshToggle).not.toBeChecked()
  })

  it('displays last activity time', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Последняя активность:')).toBeInTheDocument()
  })

  it('shows sparklines for metrics visualization', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    // Sparklines should be present in metrics cards
    const sparklineContainers = screen.getAllByTestId(/activity-sparkline/)
    expect(sparklineContainers.length).toBeGreaterThan(0)
  })
})