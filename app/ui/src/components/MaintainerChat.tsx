import React, { useState, useEffect, useRef } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { ToggleGroup } from '@/shadcn/ui/toggle-group'
import { 
  MessageCircle, 
  Send, 
  Bot, 
  User,
  FileText,
  Coins,
  Settings,
  Wrench,
  Briefcase
} from 'lucide-react'
import { post as apiPost } from '@/lib/api'
import SecretModal from '@/components/SecretModal'
import { useUIStore } from '@/state/uiStore'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ChatContext {
  capsule?: string
  policies?: string[]
  limits?: Record<string, any>
}

const MaintainerChat: React.FC = () => {
  const { analystType, setAnalystType } = useUIStore()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(
    typeof window !== 'undefined' ? localStorage.getItem('ff_chat_session_id') : null
  )
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [context, setContext] = useState<ChatContext>({
    capsule: 'Feature Factory v1.0',
    policies: [
      'Бюджет токенов: 1M в день',
      'Очередь задач: FIFO',
      'Приоритеты: HIGH > MED > LOW'
    ],
    limits: {
      'Dev': { daily: 500000, used: 300000 },
      'QA': { daily: 300000, used: 150000 },
      'Scribe': { daily: 200000, used: 100000 }
    }
  })
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const ws = useRef<WebSocket | null>(null) // Ссылка на WebSocket
  const [secretOpen, setSecretOpen] = useState(false)
  const [secretItems, setSecretItems] = useState<Array<{ key: string; hint?: string; required?: boolean; scope?: string }>>([])
  const [readinessScore, setReadinessScore] = useState<number | null>(null)
  const [missingHints, setMissingHints] = useState<string[]>([])
  const [featureCreatedId, setFeatureCreatedId] = useState<string | null>(null)

  // Опции переключателя типа аналитика
  const analystOptions = [
    {
      value: 'BUSINESS',
      label: 'Бизнес-задача',
      icon: <Briefcase className="h-4 w-4" />
    },
    {
      value: 'INTERNAL',
      label: 'Внутренняя задача', 
      icon: <Wrench className="h-4 w-4" />
    }
  ]

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Управление WebSocket-соединением
  useEffect(() => {
    // Определяем URL WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/v1/chat/maintainer` // НОВЫЙ ЭНДПОИНТ

    ws.current = new WebSocket(wsUrl)

    ws.current.onopen = () => {
      console.log('WebSocket connected')
      // Отправляем handshake с существующим session_id или без него
      const handshakeMessage = {
        type: 'handshake',
        session_id: sessionId, // Может быть null для новой сессии
        analyst_type: analystType
      }
      ws.current?.send(JSON.stringify(handshakeMessage))
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message received:', data)

      if (data.type === 'connected') {
        // Обработка handshake ответа
        console.log(`WebSocket session established: ${data.session_id}`)
        setSessionId(data.session_id)
        if (typeof window !== 'undefined') {
          localStorage.setItem('ff_chat_session_id', data.session_id)
        }
        // Восстанавливаем историю сообщений
        if (data.history) {
          const formattedHistory: ChatMessage[] = data.history.map((msg: any, index: number) => ({
            id: `${Date.now()}-${index}`,
            role: msg.role,
            content: msg.content,
            timestamp: new Date().toISOString()
          }))
          setMessages(formattedHistory)
        }
        setIsLoading(false)
        return
      }

      setIsLoading(false)

      if (data.type === 'error') {
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || 'Произошла ошибка на сервере.',
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMessage])
      } else if (data.history) {
        // Обновляем историю сообщений
        const formattedHistory: ChatMessage[] = data.history.map((msg: any, index: number) => ({
          id: `${Date.now()}-${index}`,
          role: msg.role,
          content: msg.content,
          timestamp: new Date().toISOString()
        }))
        setMessages(formattedHistory)
        
        // Сохраняем session_id, если он пришел
        if (data.session_id && data.session_id !== sessionId) {
          setSessionId(data.session_id)
          if (typeof window !== 'undefined') {
            localStorage.setItem('ff_chat_session_id', data.session_id)
          }
        }
      }

      // Обработка action (REQUEST_SECRETS)
      const action = data.action
      if (action && action.type === 'REQUEST_SECRETS') {
        const items = Array.isArray(action.items) ? action.items : []
        if (items.length > 0) {
          setSecretItems(items)
          setSecretOpen(true)
        }
      }

      // Примерная готовность (REST может прислать readiness_score; WS — нет)
      const rs = typeof data.readiness_score === 'number'
        ? data.readiness_score
        : (action?.type === 'REQUEST_SECRETS' ? 0.5 : (action?.type === 'FINALIZE_AND_CREATE_FEATURE' ? 0.9 : 0.6))
      if (!Number.isNaN(rs)) setReadinessScore(rs)

      // Подсказки по недостающим полям: парсим из последнего ответа
      const lastText: string | undefined = data.response || (data.history && data.history.length > 0 ? data.history[data.history.length - 1]?.content : undefined)
      const hints: string[] = []
      if (typeof lastText === 'string') {
        // Ищем "Нужны уточнения по: ..."
        const m1 = lastText.match(/Нужны уточнения по:\s*([^\.\n]+)/i)
        if (m1 && m1[1]) {
          m1[1].split(',').forEach((x) => {
            const t = x.trim()
            if (t) hints.push(t)
          })
        }
        // Ищем сообщения про схему intent
        const m2 = lastText.match(/проверка схемы intent не пройдена:?\s*([^\.\n]+)/i)
        if (m2 && m2[1]) {
          const frag = m2[1].replace(/['"\[\]]/g, '').trim()
          if (frag) hints.push(frag)
        }
        // Ищем номер задачи
        const m3 = lastText.match(/Номер задачи\D+(\d+)/i)
        if (m3 && m3[1]) {
          setFeatureCreatedId(m3[1])
        }
      }
      setMissingHints(hints)
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
      setIsLoading(false)
      // Можно добавить логику переподключения
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsLoading(false)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Произошла ошибка соединения с чатом. Пожалуйста, обновите страницу.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    }

    // Очистка при размонтировании компонента
    return () => {
      ws.current?.close()
    }
  }, []) // Пустой массив зависимостей означает, что эффект запустится один раз при монтировании

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const messagePayload = {
        message: inputValue,
        session_id: sessionId, // Session ID для persistent соединения с LLM
        analyst_type: analystType
      }
      ws.current.send(JSON.stringify(messagePayload))
    } else {
      console.error('WebSocket is not open.')
      setIsLoading(false)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Соединение с чатом не установлено. Пожалуйста, попробуйте еще раз или обновите страницу.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleRequestFinalize = async () => {
    if (isLoading) return
    const text = 'Готово, пожалуйста, финализируй и создай задачу'
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const payload = { message: text, session_id: sessionId, analyst_type: analystType }
      ws.current.send(JSON.stringify(payload))
    } else {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-200px)] gap-6">
      <SecretModal
        open={secretOpen}
        items={secretItems}
        onClose={() => setSecretOpen(false)}
        onSubmit={async (values) => {
          try {
            for (const [key, v] of Object.entries(values)) {
              await apiPost('/secrets/upsert', { key, value: v.value, scope: v.scope || 'test' })
              const okMsg: ChatMessage = {
                id: `${Date.now()}-${key}`,
                role: 'assistant',
                content: `Секрет ${key} принят и сохранён (маскировано).`,
                timestamp: new Date().toISOString()
              }
              setMessages(prev => [...prev, okMsg])
            }
          } catch (e: any) {
            const errMsg: ChatMessage = {
              id: `${Date.now()}-err`,
              role: 'assistant',
              content: `Не удалось сохранить секреты: ${e?.message || 'ошибка'}`,
              timestamp: new Date().toISOString()
            }
            setMessages(prev => [...prev, errMsg])
          } finally {
            setSecretOpen(false)
          }
        }}
      />
      {/* Chat Messages */}
      <div className="flex-1 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="flex flex-col gap-3 pb-3">
            <div className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium">Чат с Продуктом</CardTitle>
              <MessageCircle className="h-4 w-4 text-muted-foreground" />
            </div>
            
            {/* Переключатель типа аналитика */}
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-muted-foreground">Тип задачи:</span>
              <ToggleGroup
                options={analystOptions}
                value={analystType}
                onValueChange={(value) => setAnalystType(value as 'INTERNAL' | 'BUSINESS')}
              />
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            <div className="flex-1 p-4 overflow-y-auto">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div 
                    key={message.id} 
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div 
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.role === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-100 dark:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {message.role === 'assistant' ? (
                          <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />
                        ) : (
                          <User className="h-4 w-4 mt-0.5 flex-shrink-0" />
                        )}
                        <div>
                          <p className="text-sm">{message.content}</p>
                          <p className={`text-xs mt-1 ${
                            message.role === 'user' 
                              ? 'text-blue-100' 
                              : 'text-gray-500 dark:text-gray-400'
                          }`}>
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </p>
                          {/* Бейдж готовности и подсказки для ассистента (только у последнего ответа) */}
                          {message.role === 'assistant' && message.id === messages[messages.length - 1]?.id && (
                            <div className="mt-2 space-y-1">
                              {typeof readinessScore === 'number' && (
                                <span className="inline-flex items-center text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                                  Готовность: {readinessScore.toFixed(2)}
                                </span>
                              )}
                              {!!missingHints.length && (
                                <div className="text-xs text-amber-700 dark:text-amber-300">
                                  Недостаёт: {missingHints.join(', ')}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4 mt-0.5" />
                        <div className="flex space-x-1">
                          <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
            
            {/* Input Area */}
            <div className="border-t p-4">
              <div className="flex gap-2 items-center">
                <Input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Введите ваше сообщение..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button 
                  onClick={handleSend} 
                  disabled={!inputValue.trim() || isLoading}
                  size="icon"
                  data-testid="btn-send"
                >
                  <Send className="h-4 w-4" />
                </Button>
                {typeof readinessScore === 'number' && readinessScore >= 0.85 && (
                  <Button variant="outline" onClick={handleRequestFinalize} disabled={isLoading} data-testid="btn-request-finalize">
                    Попросить финализацию
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Context Panel */}
      <div className="w-80 hidden lg:block">
        <Card className="h-full flex flex-col">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Контекст</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto">
            <div className="space-y-6">
              {/* Capsule */}
              <div>
                <h3 className="text-sm font-medium mb-2 flex items-center">
                  <FileText className="h-4 w-4 mr-2" />
                  Capsule
                </h3>
                <p className="text-sm text-muted-foreground">
                  {context.capsule}
                </p>
              </div>
              
              {/* Policies */}
              <div>
                <h3 className="text-sm font-medium mb-2">Политики</h3>
                <ul className="space-y-2">
                  {context.policies?.map((policy, index) => (
                    <li key={index} className="text-sm text-muted-foreground flex items-start">
                      <span className="mr-2"> • </span>
                      <span>{policy}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              {/* Limits */}
              <div>
                <h3 className="text-sm font-medium mb-2 flex items-center">
                  <Coins className="h-4 w-4 mr-2" />
                  Лимиты
                </h3>
                <div className="space-y-3">
                  {Object.entries(context.limits || {}).map(([role, limit]) => (
                    <div key={role} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{role}</span>
                        <span>{limit.used.toLocaleString()}/{limit.daily.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5 dark:bg-gray-700">
                        <div 
                          className="bg-blue-600 h-1.5 rounded-full" 
                          style={{ width: `${(limit.used / limit.daily) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Toast: создана задача */}
      {featureCreatedId && (
        <div className="fixed bottom-4 right-4 z-50" data-testid="toast-feature-created">
          <div className="bg-white dark:bg-gray-800 border rounded shadow-lg px-4 py-3 text-sm">
            <div className="font-medium mb-1">Задача создана</div>
            <div className="mb-2">Номер: {featureCreatedId}</div>
            <div className="flex gap-2 justify-end">
              <a href={`/features/${featureCreatedId}`} className="text-blue-600 hover:underline">Перейти</a>
              <button className="text-gray-500 hover:text-gray-700" onClick={() => setFeatureCreatedId(null)}>Закрыть</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MaintainerChat
