import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/shadcn/ui/button'
import { Textarea } from '@/shadcn/ui/textarea'
import { 
  Send, 
  Sparkles,
  Play,
  FileText,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader
} from 'lucide-react'
import { formatRole, formatDate, formatFeatureStatus } from '@/lib/format'
import { MaintainerIntent, MaintainerPlan, Feature } from '@/lib/types'
import { CodeBlock } from '@/shadcn/ui/code-block'
import { StatusPill } from '@/shadcn/ui/status-pill'

interface ChatMessage {
  id: string
  type: 'user' | 'intent' | 'plan' | 'feature_created' | 'error'
  content: string | MaintainerIntent | MaintainerPlan | Feature
  timestamp: string
}

interface ChatPaneProps {
  onGenerateIntent?: (nlText: string) => Promise<MaintainerIntent | null>
  onGeneratePlan?: (intent: MaintainerIntent) => Promise<MaintainerPlan | null>
  onCreateFeature?: (intent: MaintainerIntent) => Promise<Feature | null>
  onExecutePlan?: (plan: MaintainerPlan) => Promise<boolean>
  className?: string
}

const ChatPane: React.FC<ChatPaneProps> = ({ 
  onGenerateIntent,
  onGeneratePlan,
  onCreateFeature,
  onExecutePlan,
  className 
}) => {
  const [inputValue, setInputValue] = useState('')
  const [isGeneratingIntent, setIsGeneratingIntent] = useState(false)
  const [generatedIntent, setGeneratedIntent] = useState<MaintainerIntent | null>(null)
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false)
  const [generatedPlan, setGeneratedPlan] = useState<MaintainerPlan | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value)
  }
  
  // Handle send message
  const handleSendMessage = async () => {
    if (inputValue.trim() === '') return
    
    // Add user message to chat
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    
    // Generate intent if callback is provided
    if (onGenerateIntent) {
      setIsGeneratingIntent(true)
      try {
        const intent = await onGenerateIntent(inputValue)
        if (intent) {
          setGeneratedIntent(intent)
          
          // Add intent message to chat
          const intentMessage: ChatMessage = {
            id: `msg-${Date.now()}`,
            type: 'intent',
            content: intent,
            timestamp: new Date().toISOString()
          }
          
          setMessages(prev => [...prev, intentMessage])
        }
      } catch (error) {
        console.error('Error generating intent:', error)
        
        // Add error message to chat
        const errorMessage: ChatMessage = {
          id: `msg-${Date.now()}`,
          type: 'error',
          content: 'Ошибка при генерации интента',
          timestamp: new Date().toISOString()
        }
        
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setIsGeneratingIntent(false)
      }
    }
  }
  
  // Generate plan from intent
  const handleGeneratePlan = async (intent: MaintainerIntent) => {
    if (!onGeneratePlan) return
    
    setIsGeneratingPlan(true)
    try {
      const plan = await onGeneratePlan(intent)
      if (plan) {
        setGeneratedPlan(plan)
        
        // Add plan message to chat
        const planMessage: ChatMessage = {
          id: `msg-${Date.now()}`,
          type: 'plan',
          content: plan,
          timestamp: new Date().toISOString()
        }
        
        setMessages(prev => [...prev, planMessage])
      }
    } catch (error) {
      console.error('Error generating plan:', error)
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        type: 'error',
        content: 'Ошибка при генерации плана',
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsGeneratingPlan(false)
    }
  }
  
  // Create feature from intent
  const handleCreateFeature = async (intent: MaintainerIntent) => {
    if (!onCreateFeature) return
    
    try {
      const feature = await onCreateFeature(intent)
      if (feature) {
        // Add feature created message to chat
        const featureMessage: ChatMessage = {
          id: `msg-${Date.now()}`,
          type: 'feature_created',
          content: feature,
          timestamp: new Date().toISOString()
        }
        
        setMessages(prev => [...prev, featureMessage])
        
        // Clear generated intent and plan
        setGeneratedIntent(null)
        setGeneratedPlan(null)
      }
    } catch (error) {
      console.error('Error creating feature:', error)
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        type: 'error',
        content: 'Ошибка при создании фичи',
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, errorMessage])
    }
  }
  
  // Execute plan immediately
  const handleExecutePlan = async (plan: MaintainerPlan) => {
    if (!onExecutePlan) return
    
    try {
      const success = await onExecutePlan(plan)
      if (success) {
        // Add success message to chat
        const successMessage: ChatMessage = {
          id: `msg-${Date.now()}`,
          type: 'feature_created',
          content: 'План выполнен успешно',
          timestamp: new Date().toISOString()
        }
        
        setMessages(prev => [...prev, successMessage])
        
        // Clear generated intent and plan
        setGeneratedIntent(null)
        setGeneratedPlan(null)
      }
    } catch (error) {
      console.error('Error executing plan:', error)
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        type: 'error',
        content: 'Ошибка при выполнении плана',
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, errorMessage])
    }
  }
  
  // Handle key press (Enter to send, Shift+Enter for new line)
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }
  
  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto border rounded-lg p-4 mb-4 bg-white dark:bg-gray-800">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Sparkles className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Начните диалог</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Введите ваш запрос на естественном языке для генерации фичи
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div 
                key={message.id} 
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-3/4 rounded-lg p-4 ${
                    message.type === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : message.type === 'error'
                      ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                  }`}
                >
                  {message.type === 'user' && (
                    <div>
                      <div className="font-medium">Вы</div>
                      <div className="mt-1">{message.content as string}</div>
                      <div className="mt-2 text-xs opacity-70">
                        {formatDate(message.timestamp)}
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'intent' && (
                    <div>
                      <div className="flex items-center font-medium">
                        <Sparkles className="h-4 w-4 mr-2" />
                        Сгенерированный интент
                      </div>
                      <div className="mt-2">
                        <CodeBlock 
                          code={JSON.stringify((message.content as MaintainerIntent).intent_json, null, 2)} 
                          language="json"
                        />
                      </div>
                      {(message.content as MaintainerIntent).issues.length > 0 && (
                        <div className="mt-2">
                          <div className="font-medium text-sm">Проблемы:</div>
                          <ul className="list-disc list-inside text-sm">
                            {(message.content as MaintainerIntent).issues.map((issue, idx) => (
                              <li key={idx}>{issue}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {(message.content as MaintainerIntent).suggestions.length > 0 && (
                        <div className="mt-2">
                          <div className="font-medium text-sm">Предложения:</div>
                          <ul className="list-disc list-inside text-sm">
                            {(message.content as MaintainerIntent).suggestions.map((suggestion, idx) => (
                              <li key={idx}>{suggestion}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div className="mt-2 text-xs opacity-70">
                        {formatDate(message.timestamp)}
                      </div>
                      <div className="mt-3 flex space-x-2">
                        <Button 
                          size="sm" 
                          onClick={() => handleGeneratePlan(message.content as MaintainerIntent)}
                          disabled={isGeneratingPlan || !onGeneratePlan}
                        >
                          {isGeneratingPlan ? (
                            <>
                              <Loader className="mr-2 h-4 w-4 animate-spin" />
                              Генерация плана...
                            </>
                          ) : (
                            <>
                              <Play className="mr-2 h-4 w-4" />
                              Сгенерировать план
                            </>
                          )}
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleCreateFeature(message.content as MaintainerIntent)}
                          disabled={!onCreateFeature}
                        >
                          <FileText className="mr-2 h-4 w-4" />
                          Создать фичу
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'plan' && (
                    <div>
                      <div className="flex items-center font-medium">
                        <Play className="h-4 w-4 mr-2" />
                        Сгенерированный план
                      </div>
                      <div className="mt-2">
                        <div className="font-medium">DAG:</div>
                        <ul className="list-disc list-inside space-y-1">
                          {(message.content as MaintainerPlan).dag.map((task, idx) => (
                            <li key={idx} className="text-sm">
                              <span className="font-medium">{formatRole(task.role)}</span>: {task.name}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="mt-2">
                        <div className="font-medium">Package Contract:</div>
                        <CodeBlock 
                          code={JSON.stringify((message.content as MaintainerPlan).package_contract, null, 2)} 
                          language="json"
                        />
                      </div>
                      <div className="mt-2 text-xs opacity-70">
                        {formatDate(message.timestamp)}
                      </div>
                      <div className="mt-3 flex space-x-2">
                        <Button 
                          size="sm" 
                          onClick={() => handleExecutePlan(message.content as MaintainerPlan)}
                          disabled={!onExecutePlan}
                        >
                          <Play className="mr-2 h-4 w-4" />
                          Выполнить план
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'feature_created' && (
                    <div>
                      <div className="flex items-center font-medium text-green-600 dark:text-green-400">
                        <CheckCircle className="h-4 w-4 mr-2" />
                        {typeof message.content === 'string' 
                          ? message.content 
                          : 'Фича создана'}
                      </div>
                      {typeof message.content !== 'string' && (
                        <div className="mt-2">
                          <div className="font-medium">
                            {(message.content as Feature).title}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-300">
                            ID: {(message.content as Feature).id} | 
                            Статус: <StatusPill variant={
                              (message.content as Feature).status === 'NEW' ? 'default' :
                              (message.content as Feature).status === 'PLANNED' ? 'secondary' :
                              (message.content as Feature).status === 'RUNNING' ? 'warning' :
                              (message.content as Feature).status === 'DONE' ? 'success' :
                              'destructive'
                            }>
                              {formatFeatureStatus((message.content as Feature).status)}
                            </StatusPill>
                          </div>
                        </div>
                      )}
                      <div className="mt-2 text-xs opacity-70">
                        {formatDate(message.timestamp)}
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'error' && (
                    <div>
                      <div className="flex items-center font-medium text-red-600 dark:text-red-400">
                        <XCircle className="h-4 w-4 mr-2" />
                        Ошибка
                      </div>
                      <div className="mt-1">{message.content as string}</div>
                      <div className="mt-2 text-xs opacity-70">
                        {formatDate(message.timestamp)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border rounded-lg p-4 bg-white dark:bg-gray-800">
        <div className="flex">
          <Textarea
            placeholder="Опишите фичу на естественном языке..."
            className="flex-1 resize-none"
            rows={3}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            disabled={isGeneratingIntent || isGeneratingPlan}
          />
          <div className="ml-3 flex items-end">
            <Button 
              onClick={handleSendMessage} 
              disabled={inputValue.trim() === '' || isGeneratingIntent || isGeneratingPlan || !onGenerateIntent}
            >
              {isGeneratingIntent ? (
                <>
                  <Loader className="mr-2 h-4 w-4 animate-spin" />
                  Генерация...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </div>
        <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Нажмите Enter для отправки, Shift+Enter для новой строки
        </div>
      </div>
    </div>
  )
}

export { ChatPane }