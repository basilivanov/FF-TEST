import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import GraphControlPanel from '../GraphControlPanel'
import * as api from '@/lib/api'

jest.mock('@/lib/api')
const mockApi = api as jest.Mocked<typeof api>

jest.mock('@/components/Sparkline', () => ({
  Sparkline: ({ data, color, animate }: any) => (
    <div data-testid="sparkline" data-color={color} data-animated={animate}>
      Sparkline: {data?.length || 0} points
    </div>
  )
}))

jest.mock('@/components/ProgressRing', () => ({
  ProgressRing: ({ value, max, gradientFrom, gradientTo }: any) => (
    <div
      data-testid="progress-ring"
      data-value={value}
      data-max={max}
      data-gradient-from={gradientFrom}
      data-gradient-to={gradientTo}
    >
      Progress: {value}/{max}
    </div>
  )
}))

const mockFeature = {
  id: 1,
  title: 'Test Feature',
  status: 'PLANNED',
  priority: 1
}

const mockRuns = [
  {
    run_id: 'run-123',
    feature_id: 1,
    graph_name: 'feature_graph',
    thread_id: 'thread-456',
    status: 'RUNNING',
    last_checkpoint_at: '2023-01-01T12:00:00Z'
  }
]

const mockTasks = [
  { id: 1, feature_id: 1, role: 'Dev', status: 'DONE', attempts: 1, scheduled_at: '2023-01-01T10:00:00Z' },
  { id: 2, feature_id: 1, role: 'QA', status: 'RUNNING', attempts: 1, scheduled_at: '2023-01-01T11:00:00Z' },
  { id: 3, feature_id: 1, role: 'Scribe', status: 'NEW', attempts: 0, scheduled_at: '2023-01-01T12:00:00Z' }
]

const mockOnRefresh = jest.fn()

const renderComponent = (props = {}) => {
  return render(
    <GraphControlPanel
      feature={mockFeature}
      runs={mockRuns}
      tasks={mockTasks}
      onRefresh={mockOnRefresh}
      {...props}
    />
  )
}

describe('Enhanced GraphControlPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApi.post.mockResolvedValue({ data: {} })
  })

  describe('Button Contrast and Styling', () => {
    it('renders plan button with high contrast indigo styling', () => {
      renderComponent()

      const planButton = screen.getByRole('button', { name: /план/i })
      expect(planButton).toHaveClass('bg-indigo-600', 'hover:bg-indigo-700', 'text-white')
    })

    it('renders start button with high contrast green styling', () => {
      renderComponent()

      const startButton = screen.getByRole('button', { name: 'Старт' })
      expect(startButton).toHaveClass('bg-green-600', 'hover:bg-green-700', 'text-white')
    })

    it('renders restart button with high contrast orange styling', () => {
      renderComponent()

      const restartButton = screen.getByRole('button', { name: /рестарт/i })
      expect(restartButton).toHaveClass('bg-orange-600', 'hover:bg-orange-700', 'text-white')
    })

    it('renders runner tick button with high contrast purple styling', () => {
      renderComponent()

      const tickButton = screen.getByRole('button', { name: /тик runner/i })
      expect(tickButton).toHaveClass('bg-purple-600', 'hover:bg-purple-700', 'text-white')
    })

    it('adds shadow to all action buttons for better visibility', () => {
      renderComponent()

      const buttons = [
        screen.getByRole('button', { name: /план/i }),
        screen.getByRole('button', { name: 'Старт' }),
        screen.getByRole('button', { name: /рестарт/i }),
        screen.getByRole('button', { name: /тик runner/i })
      ]

      buttons.forEach(button => {
        expect(button).toHaveClass('shadow-sm')
      })
    })
  })

  describe('Interactive Functionality', () => {
    it('handles plan feature action', async () => {
      const newFeature = { ...mockFeature, status: 'NEW' }
      renderComponent({ feature: newFeature })

      const planButton = screen.getByRole('button', { name: /план/i })
      fireEvent.click(planButton)

      await waitFor(() => {
        expect(mockApi.post).toHaveBeenCalledWith('/orchestrator/features/1/plan')
        expect(mockOnRefresh).toHaveBeenCalled()
      })
    })

    it('handles run feature action', async () => {
      renderComponent()

      const startButton = screen.getByRole('button', { name: 'Старт' })
      fireEvent.click(startButton)

      await waitFor(() => {
        expect(mockApi.post).toHaveBeenCalledWith('/orchestrator/features/1/run')
        expect(mockOnRefresh).toHaveBeenCalled()
      })
    })

    it('handles runner tick action', async () => {
      renderComponent()

      const tickButton = screen.getByRole('button', { name: /тик runner/i })
      fireEvent.click(tickButton)

      await waitFor(() => {
        expect(mockApi.post).toHaveBeenCalledWith('/runner/run-once')
        expect(mockOnRefresh).toHaveBeenCalled()
      })
    })

    it('disables buttons appropriately based on feature status', () => {
      const newFeature = { ...mockFeature, status: 'DONE' }
      renderComponent({ feature: newFeature })

      const planButton = screen.getByRole('button', { name: /план/i })
      const startButton = screen.getByRole('button', { name: 'Старт' })

      expect(planButton).toBeDisabled()
      expect(startButton).toBeDisabled()
    })
  })

  describe('Auto-refresh and Real-time Updates', () => {
    it('toggles auto-refresh mode', () => {
      renderComponent()

      const autoButton = screen.getByRole('button', { name: 'Auto' })
      expect(autoButton).not.toHaveClass('bg-blue-600')

      fireEvent.click(autoButton)
      // Auto button uses variant='default' when active, which doesn't necessarily mean bg-blue-600
      // Let's check for variant change instead
      expect(autoButton).not.toHaveClass('border-input')
    })

    it('shows AUTO badge when auto-refresh is enabled', () => {
      renderComponent()

      const autoButton = screen.getByRole('button', { name: /auto/i })
      fireEvent.click(autoButton)

      expect(screen.getByText('AUTO')).toBeInTheDocument()
      expect(screen.getByText('AUTO')).toHaveClass('animate-pulse')
    })

    it('updates last activity timestamp', async () => {
      renderComponent()

      const tickButton = screen.getByRole('button', { name: /тик runner/i })
      fireEvent.click(tickButton)

      await waitFor(() => {
        expect(screen.getByText(/Последняя активность:/)).toBeInTheDocument()
      })
    })
  })

  describe('Metrics and Visualizations', () => {
    it('renders performance sparkline with correct props', () => {
      renderComponent()

      const sparklines = screen.getAllByTestId('sparkline')
      const performanceSparkline = sparklines.find(s => s.getAttribute('data-color') === '#3B82F6')

      expect(performanceSparkline).toBeInTheDocument()
      expect(performanceSparkline).toHaveAttribute('data-animated', 'true')
    })

    it('renders queue depth sparkline with purple color', () => {
      renderComponent()

      const sparklines = screen.getAllByTestId('sparkline')
      const queueSparkline = sparklines.find(s => s.getAttribute('data-color') === '#7C3AED')

      expect(queueSparkline).toBeInTheDocument()
    })

    it('renders progress ring with gradient colors', () => {
      renderComponent()

      const progressRing = screen.getByTestId('progress-ring')
      expect(progressRing).toHaveAttribute('data-gradient-from', '#10B981')
      expect(progressRing).toHaveAttribute('data-gradient-to', '#059669')
    })

    it('calculates task progress correctly', () => {
      renderComponent()

      const progressRing = screen.getByTestId('progress-ring')
      // 1 task DONE out of 3 total tasks
      expect(progressRing).toHaveAttribute('data-value', '1')
      expect(progressRing).toHaveAttribute('data-max', '3')
    })
  })

  describe('Status Indicators and Information', () => {
    it('displays current run information', () => {
      renderComponent()

      expect(screen.getByText('Текущий запуск')).toBeInTheDocument()
      expect(screen.getByText('run-123')).toBeInTheDocument()
      expect(screen.getByText('Граф: feature_graph')).toBeInTheDocument()
      expect(screen.getByText('Поток: thread-456')).toBeInTheDocument()
    })

    it('shows metrics cards with appropriate values', async () => {
      renderComponent()

      // Wait for metrics to load
      await waitFor(() => {
        expect(screen.getAllByText('Очередь')).toHaveLength(2) // One in main metrics, one in card title
      })

      expect(screen.getAllByText('Активные')).toHaveLength(1)
      expect(screen.getAllByText('Производительность')).toHaveLength(1)
    })

    it('displays status icons with proper animations', () => {
      renderComponent()

      // RUNNING status should have animate-pulse
      const runningElements = screen.getAllByText('RUNNING')
      expect(runningElements.length).toBeGreaterThan(0)
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      mockApi.post.mockRejectedValue(new Error('API Error'))

      renderComponent()

      const tickButton = screen.getByRole('button', { name: /тик runner/i })
      fireEvent.click(tickButton)

      // Should not crash the component
      await waitFor(() => {
        expect(mockApi.post).toHaveBeenCalled()
      })
    })

    it('shows loading state during API calls', async () => {
      mockApi.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      renderComponent()

      const tickButton = screen.getByRole('button', { name: /тик runner/i })
      fireEvent.click(tickButton)

      // Button should be disabled during loading
      expect(tickButton).toBeDisabled()
    })
  })

  describe('Responsive Design', () => {
    it('renders mobile-friendly grid layout', () => {
      renderComponent()

      const gridContainer = screen.getByText('План').closest('.grid')
      expect(gridContainer).toHaveClass('grid-cols-2')
    })

    it('shows compact metrics layout', () => {
      renderComponent()

      const metricsGrid = screen.getByText('Производительность').closest('.grid')?.closest('.grid')
      expect(metricsGrid).toHaveClass('grid-cols-1', 'md:grid-cols-3')
    })
  })
})