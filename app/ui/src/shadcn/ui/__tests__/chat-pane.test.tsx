import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatPane } from '@/shadcn/ui/chat-pane'

describe('ChatPane', () => {
  const mockIntent = {
    nl_text: 'Test intent',
    intent_json: { action: 'test' },
    issues: [],
    suggestions: []
  }

  const mockPlan = {
    intent_json: { action: 'test' },
    dag: [{ role: 'Dev', name: 'task1' }],
    package_contract: {}
  }

  const mockFeature = {
    id: 1,
    title: 'Test Feature',
    intent_json: { action: 'test' },
    status: 'NEW',
    priority: 1,
    created_at: '2023-01-01T00:00:00Z',
    created_by: 'test',
    env: 'test'
  }

  it('renders empty chat state', () => {
    render(<ChatPane />)
    
    expect(screen.getByText('Начните диалог')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Опишите фичу на естественном языке...')).toBeInTheDocument()
  })

  it('allows user to send a message', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    expect(screen.getByText('Test message')).toBeInTheDocument()
    
    await waitFor(() => {
      expect(mockGenerateIntent).toHaveBeenCalledWith('Test message')
    })
  })

  it('displays generated intent', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
  })

  it('handles intent generation error', async () => {
    const mockGenerateIntent = jest.fn().mockRejectedValue(new Error('Test error'))
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Ошибка при генерации интента')).toBeInTheDocument()
    })
  })

  it('allows generating plan from intent', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockGeneratePlan = jest.fn().mockResolvedValue(mockPlan)
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onGeneratePlan={mockGeneratePlan}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    await waitFor(() => {
      expect(mockGeneratePlan).toHaveBeenCalledWith(mockIntent)
    })
  })

  it('displays generated plan', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockGeneratePlan = jest.fn().mockResolvedValue(mockPlan)
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onGeneratePlan={mockGeneratePlan}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный план')).toBeInTheDocument()
    })
  })

  it('handles plan generation error', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockGeneratePlan = jest.fn().mockRejectedValue(new Error('Test error'))
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onGeneratePlan={mockGeneratePlan}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    await waitFor(() => {
      expect(screen.getByText('Ошибка при генерации плана')).toBeInTheDocument()
    })
  })

  it('allows creating feature from intent', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockCreateFeature = jest.fn().mockResolvedValue(mockFeature)
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onCreateFeature={mockCreateFeature}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const createFeatureButton = screen.getByRole('button', { name: 'Создать фичу' })
    fireEvent.click(createFeatureButton)
    
    await waitFor(() => {
      expect(mockCreateFeature).toHaveBeenCalledWith(mockIntent)
    })
  })

  it('displays created feature', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockCreateFeature = jest.fn().mockResolvedValue(mockFeature)
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onCreateFeature={mockCreateFeature}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const createFeatureButton = screen.getByRole('button', { name: 'Создать фичу' })
    fireEvent.click(createFeatureButton)
    
    await waitFor(() => {
      expect(screen.getByText('Фича создана')).toBeInTheDocument()
      expect(screen.getByText('Test Feature')).toBeInTheDocument()
    })
  })

  it('handles feature creation error', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockCreateFeature = jest.fn().mockRejectedValue(new Error('Test error'))
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onCreateFeature={mockCreateFeature}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const createFeatureButton = screen.getByRole('button', { name: 'Создать фичу' })
    fireEvent.click(createFeatureButton)
    
    await waitFor(() => {
      expect(screen.getByText('Ошибка при создании фичи')).toBeInTheDocument()
    })
  })

  it('allows executing plan', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockGeneratePlan = jest.fn().mockResolvedValue(mockPlan)
    const mockExecutePlan = jest.fn().mockResolvedValue(true)
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onGeneratePlan={mockGeneratePlan}
        onExecutePlan={mockExecutePlan}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный план')).toBeInTheDocument()
    })
    
    const executePlanButton = screen.getByRole('button', { name: 'Выполнить план' })
    fireEvent.click(executePlanButton)
    
    await waitFor(() => {
      expect(mockExecutePlan).toHaveBeenCalledWith(mockPlan)
    })
  })

  it('displays plan execution result', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockGeneratePlan = jest.fn().mockResolvedValue(mockPlan)
    const mockExecutePlan = jest.fn().mockResolvedValue(true)
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onGeneratePlan={mockGeneratePlan}
        onExecutePlan={mockExecutePlan}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный план')).toBeInTheDocument()
    })
    
    const executePlanButton = screen.getByRole('button', { name: 'Выполнить план' })
    fireEvent.click(executePlanButton)
    
    await waitFor(() => {
      expect(screen.getByText('План выполнен успешно')).toBeInTheDocument()
    })
  })

  it('handles plan execution error', async () => {
    const mockGenerateIntent = jest.fn().mockResolvedValue(mockIntent)
    const mockGeneratePlan = jest.fn().mockResolvedValue(mockPlan)
    const mockExecutePlan = jest.fn().mockRejectedValue(new Error('Test error'))
    
    render(
      <ChatPane 
        onGenerateIntent={mockGenerateIntent}
        onGeneratePlan={mockGeneratePlan}
        onExecutePlan={mockExecutePlan}
      />
    )
    
    const textarea = screen.getByPlaceholderText('Опишите фичу на естественном языке...')
    const sendButton = screen.getByRole('button', { name: 'Send' })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный интент')).toBeInTheDocument()
    })
    
    const generatePlanButton = screen.getByRole('button', { name: 'Сгенерировать план' })
    fireEvent.click(generatePlanButton)
    
    await waitFor(() => {
      expect(screen.getByText('Сгенерированный план')).toBeInTheDocument()
    })
    
    const executePlanButton = screen.getByRole('button', { name: 'Выполнить план' })
    fireEvent.click(executePlanButton)
    
    await waitFor(() => {
      expect(screen.getByText('Ошибка при выполнении плана')).toBeInTheDocument()
    })
  })

  it('renders with custom className', () => {
    render(<ChatPane className="custom-chat" />)
    
    const chatPane = screen.getByRole('generic', { hidden: true })
    expect(chatPane).toHaveClass('custom-chat')
  })
})