import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import GraphControlPanel from '../GraphControlPanel'

// Mock API calls
jest.mock('../../lib/api', () => ({
  post: jest.fn()
}))

// Mock Sparkline component
jest.mock('../Sparkline', () => {
  return function MockSparkline() {
    return <div data-testid="sparkline" />
  }
})

// Mock ProgressRing component
jest.mock('../ProgressRing', () => {
  return function MockProgressRing() {
    return <div data-testid="progress-ring" />
  }
})

const mockFeature = {
  id: 1,
  title: 'Test Feature',
  status: 'PLANNED',
  priority: 5
}

const mockTasks = [
  {
    id: 1,
    feature_id: 1,
    role: 'Architect',
    status: 'DONE',
    attempts: 1,
    scheduled_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 2,
    feature_id: 1,
    role: 'Dev',
    status: 'RUNNING',
    attempts: 1,
    scheduled_at: '2024-01-15T10:05:00Z'
  },
  {
    id: 3,
    feature_id: 1,
    role: 'QA',
    status: 'NEW',
    attempts: 1,
    scheduled_at: '2024-01-15T10:10:00Z'
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
    created_at: '2024-01-15T10:00:00Z'
  }
]

const { post } = require('../../lib/api')

describe('GraphControlPanel', () => {
  const mockOnRefresh = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock successful API responses
    post.mockResolvedValue({ data: {} })
  })

  it('renders control panel with feature status', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Управление графом')).toBeInTheDocument()
    expect(screen.getByText('Статус фичи')).toBeInTheDocument()
    expect(screen.getByText('PLANNED')).toBeInTheDocument()
  })

  it('displays current run information', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Текущий запуск')).toBeInTheDocument()
    expect(screen.getByText('Граф: test-graph')).toBeInTheDocument()
    expect(screen.getByText('Поток: thread-1')).toBeInTheDocument()
  })

  it('shows control buttons with correct states', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('План')).toBeInTheDocument()
    expect(screen.getByText('Старт')).toBeInTheDocument()
    expect(screen.getByText('Стоп')).toBeInTheDocument()
    expect(screen.getByText('Рестарт')).toBeInTheDocument()
    expect(screen.getByText('Тик Runner')).toBeInTheDocument()
  })

  it('enables start button for planned features', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const startButton = screen.getByText('Старт')
    expect(startButton).not.toBeDisabled()
  })

  it('disables plan button for non-new features', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const planButton = screen.getByText('План')
    expect(planButton).toBeDisabled() // PLANNED status, not NEW
  })

  it('enables stop button when run is active', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const stopButton = screen.getByText('Стоп')
    expect(stopButton).not.toBeDisabled() // Run status is RUNNING
  })

  it('calls API and refreshes when plan button is clicked', async () => {
    const newFeature = { ...mockFeature, status: 'NEW' }

    render(
      <GraphControlPanel
        feature={newFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const planButton = screen.getByText('План')
    fireEvent.click(planButton)

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/orchestrator/features/1/plan')
      expect(mockOnRefresh).toHaveBeenCalled()
    })
  })

  it('calls API and refreshes when start button is clicked', async () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const startButton = screen.getByText('Старт')
    fireEvent.click(startButton)

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/orchestrator/features/1/run')
      expect(mockOnRefresh).toHaveBeenCalled()
    })
  })

  it('calls runner tick API when tick button is clicked', async () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const tickButton = screen.getByText('Тик Runner')
    fireEvent.click(tickButton)

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/runner/run-once')
      expect(mockOnRefresh).toHaveBeenCalled()
    })
  })

  it('toggles auto refresh when auto button is clicked', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const autoButton = screen.getByText('Auto')
    fireEvent.click(autoButton)

    // После клика кнопка должна изменить вариант
    expect(autoButton).toBeInTheDocument()
  })

  it('displays metrics cards', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Производительность')).toBeInTheDocument()
    expect(screen.getByText('Ошибки')).toBeInTheDocument()
    expect(screen.getByText('Очередь')).toBeInTheDocument()
  })

  it('shows sparklines in metrics', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const sparklines = screen.getAllByTestId('sparkline')
    expect(sparklines).toHaveLength(2) // Performance and queue sparklines
  })

  it('displays progress ring', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByTestId('progress-ring')).toBeInTheDocument()
  })

  it('shows task progress breakdown', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('DONE')).toBeInTheDocument()
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
    expect(screen.getByText('NEW')).toBeInTheDocument()
  })

  it('handles feature without current run', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={[]}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.queryByText('Текущий запуск')).not.toBeInTheDocument()
  })

  it('shows last activity timestamp', () => {
    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText(/Последняя активность:/)).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    post.mockRejectedValueOnce(new Error('API Error'))

    render(
      <GraphControlPanel
        feature={mockFeature}
        runs={mockRuns}
        tasks={mockTasks}
        onRefresh={mockOnRefresh}
      />
    )

    const startButton = screen.getByText('Старт')
    fireEvent.click(startButton)

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
      // Should not crash on error
    })
  })
})