import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import TaskDetail from '../TaskDetail'
import * as api from '@/lib/api'

// Mock the API module
jest.mock('@/lib/api')
const mockApi = api as jest.Mocked<typeof api>

// Mock the chart components
jest.mock('@/components/Sparkline', () => ({
  Sparkline: ({ data, color }: any) => (
    <div data-testid="sparkline" data-color={color} data-points={data?.length}>
      Sparkline with {data?.length || 0} points
    </div>
  )
}))

jest.mock('@/components/ProgressRing', () => ({
  ProgressRing: ({ value, max }: any) => (
    <div data-testid="progress-ring" data-value={value} data-max={max}>
      Progress: {value}/{max}
    </div>
  )
}))

jest.mock('@/components/TaskTimeline', () => ({
  __esModule: true,
  default: ({ taskId }: any) => (
    <div data-testid="task-timeline" data-task-id={taskId}>
      Task Timeline for {taskId}
    </div>
  )
}))

jest.mock('@/components/Mermaid', () => ({
  __esModule: true,
  default: ({ chart }: any) => (
    <div data-testid="mermaid-chart">{chart}</div>
  )
}))

const mockTask = {
  id: '123',
  feature_id: 456,
  role: 'Dev',
  status: 'RUNNING',
  attempts: 1,
  scheduled_at: '2023-01-01T10:00:00Z',
  started_at: '2023-01-01T10:05:00Z',
  correlation_id: 'corr-123',
  context_summary: 'Test task context',
  progress_percentage: 75
}

const mockFeature = {
  id: 456,
  title: 'Test Feature'
}

const renderTaskDetail = (taskId = '123') => {
  return render(
    <MemoryRouter initialEntries={[`/tasks/${taskId}`]}>
      <Routes>
        <Route path="/tasks/:id" element={<TaskDetail />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('TaskDetail Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('shows loading state initially', () => {
    mockApi.get.mockImplementation(() => new Promise(() => {})) // Never resolves

    renderTaskDetail()

    // Loading state shows spinner animation
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('displays task information correctly', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockTask })
      .mockResolvedValueOnce({ data: mockFeature })

    renderTaskDetail()

    await waitFor(() => {
      expect(screen.getByText('Задача #123 • Dev')).toBeInTheDocument()
      expect(screen.getByText('Фича #456 • Test Feature')).toBeInTheDocument()
      expect(screen.getByText('RUNNING')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    mockApi.get.mockRejectedValue(new Error('API Error'))

    renderTaskDetail()

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch task data')).toBeInTheDocument()
    })
  })

  it('switches between tabs correctly', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockTask })
      .mockResolvedValueOnce({ data: mockFeature })

    renderTaskDetail()

    await waitFor(() => {
      expect(screen.getByTestId('task-timeline')).toBeInTheDocument()
    })

    // Switch to details tab
    fireEvent.click(screen.getByText('Детали'))
    expect(screen.getByTestId('mermaid-chart')).toBeInTheDocument()

    // Switch to artifacts tab
    fireEvent.click(screen.getByText('Артефакты'))
    expect(screen.getByText('context.json')).toBeInTheDocument()

    // Switch to metrics tab
    fireEvent.click(screen.getByText('Метрики'))
    expect(screen.getByTestId('sparkline')).toBeInTheDocument()
  })

  it('displays artifacts with correct types and actions', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockTask })
      .mockResolvedValueOnce({ data: mockFeature })

    renderTaskDetail()

    await waitFor(() => {
      fireEvent.click(screen.getByText('Артефакты'))
    })

    expect(screen.getByText('context.json')).toBeInTheDocument()
    expect(screen.getByText('task_output.md')).toBeInTheDocument()
    expect(screen.getByText('execution.log')).toBeInTheDocument()

    // Check for action buttons with title attributes
    expect(screen.getAllByTitle('View')).toHaveLength(3)
    expect(screen.getAllByTitle('Download')).toHaveLength(3)
  })

  it('shows correlation ID link when available', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockTask })
      .mockResolvedValueOnce({ data: mockFeature })

    renderTaskDetail()

    await waitFor(() => {
      fireEvent.click(screen.getByText('Детали'))
    })

    await waitFor(() => {
      expect(screen.getByDisplayValue('corr-123')).toBeInTheDocument()
      expect(screen.getByTitle('Перейти по Correlation ID')).toBeInTheDocument()
    })
  })

  it('displays performance metrics correctly', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockTask })
      .mockResolvedValueOnce({ data: mockFeature })

    renderTaskDetail()

    await waitFor(() => {
      fireEvent.click(screen.getByText('Метрики'))
    })

    expect(screen.getByText('Время выполнения')).toBeInTheDocument()
    expect(screen.getByText('Использование памяти')).toBeInTheDocument()
    expect(screen.getByText('Загрузка CPU')).toBeInTheDocument()
    expect(screen.getByText('Токены контекста')).toBeInTheDocument()
    expect(screen.getByText('Токены вывода')).toBeInTheDocument()
  })

  it('refreshes data when refresh button is clicked', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockTask })
      .mockResolvedValueOnce({ data: mockFeature })

    renderTaskDetail()

    await waitFor(() => {
      expect(screen.getByText('Задача #123 • Dev')).toBeInTheDocument()
    })

    // Reset mocks and setup new responses
    jest.clearAllMocks()
    const updatedTask = { ...mockTask, status: 'DONE' }
    mockApi.get
      .mockResolvedValueOnce({ data: updatedTask })
      .mockResolvedValueOnce({ data: mockFeature })

    fireEvent.click(screen.getByText('Обновить'))

    await waitFor(() => {
      expect(mockApi.get).toHaveBeenCalledTimes(2)
    })
  })

  it('formats dates and times correctly', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockTask })
      .mockResolvedValueOnce({ data: mockFeature })

    renderTaskDetail()

    await waitFor(() => {
      fireEvent.click(screen.getByText('Детали'))
    })

    // The dates should be formatted (exact format depends on formatDate implementation)
    expect(screen.getByText(/Запланировано:/)).toBeInTheDocument()
    expect(screen.getByText(/Начато:/)).toBeInTheDocument()
  })

  it('shows progress ring with correct values', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockTask })
      .mockResolvedValueOnce({ data: mockFeature })

    renderTaskDetail()

    await waitFor(() => {
      fireEvent.click(screen.getByText('Метрики'))
    })

    const progressRing = screen.getByTestId('progress-ring')
    expect(progressRing).toHaveAttribute('data-value', '75')
    expect(progressRing).toHaveAttribute('data-max', '100')
  })
})