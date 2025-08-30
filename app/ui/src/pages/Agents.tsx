import React, { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { 
  Bot,
  Cpu,
  Shield,
  Wifi,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  Zap,
  Download
} from 'lucide-react'
import { get, post } from '@/lib/api'

interface AgentStatus {
  model: string
  provider: string
  status: string
  oauth_ok: boolean
  tokens_used?: number
  latency_ms?: number
  checked_at: string
  expires_at: string
  binary_path?: string
  probe_command?: string
  local_config_exists?: boolean
  has_refresh_token?: boolean
  cli_error?: string
}

interface AgentsStatusResponse {
  as_of: string
  stale: boolean
  items: AgentStatus[]
  error?: string
}

const Agents: React.FC = () => {
  const [agentsStatus, setAgentsStatus] = useState<AgentsStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async (forceFresh: boolean = false) => {
    try {
      const freshParam = forceFresh ? '?fresh=1' : ''
      const response = await get<AgentsStatusResponse>(`/agents/status${freshParam}`)
      
      const data = response.data
      setAgentsStatus(data)
      setError(data.error || null)
      
    } catch (err) {
      console.error('Agents fetch error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch agents data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    
    // Сначала запускаем фоновое обновление
    try {
      await post('/agents/refresh')
    } catch (err) {
      console.warn('Background refresh failed:', err)
    }
    
    // Затем получаем свежие данные
    await fetchData(true)
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 60000) // Обновляем каждые 60 секунд для снижения нагрузки
    return () => clearInterval(interval)
  }, [])

  const getAgentIcon = (provider: string) => {
    const p = provider.toLowerCase()
    if (p.includes('claude') || p.includes('anthropic')) return <Bot className="h-5 w-5" />
    if (p.includes('gemini')) return <Zap className="h-5 w-5" />
    if (p.includes('qwen')) return <Cpu className="h-5 w-5" />
    if (p.includes('codex') || p.includes('openai')) return <Activity className="h-5 w-5" />
    return <Shield className="h-5 w-5" />
  }

  const getStatusColor = (status: string, oauthOk: boolean) => {
    if (status === 'ok' && oauthOk) return 'text-green-600'
    if (status === 'ok' && !oauthOk) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getStatusIcon = (status: string, oauthOk: boolean) => {
    if (status === 'ok' && oauthOk) return <CheckCircle className="h-4 w-4 text-green-600" />
    if (status === 'ok' && !oauthOk) return <Clock className="h-4 w-4 text-yellow-600" />
    return <XCircle className="h-4 w-4 text-red-600" />
  }

  const agents = agentsStatus?.items || []
  const isStale = agentsStatus?.stale || false

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-64 space-y-3">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <div className="text-sm text-gray-500">Загрузка состояния агентов...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Заголовок с кнопкой обновления */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">LLM Agents Status</h1>
          <div className="mt-1 flex items-center space-x-2">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Мониторинг состояния ИИ-агентов и OAuth токенов
            </p>
            {agentsStatus && (
              <Badge variant={isStale ? "destructive" : "secondary"} className="text-xs">
                {isStale ? "УСТАРЕЛО" : "АКТУАЛЬНО"} {new Date(agentsStatus.as_of).toLocaleTimeString()}
              </Badge>
            )}
          </div>
        </div>
        <Button onClick={handleRefresh} disabled={refreshing} className="w-full sm:w-auto">
          <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Обновить
        </Button>
      </div>

      {/* Сводная информация */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Bot className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Всего агентов</p>
                <p className="text-2xl font-bold">{agents.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Онлайн</p>
                <p className="text-2xl font-bold text-green-600">
                  {agents.filter(a => a.status === 'ok' && a.oauth_ok).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-yellow-500" />
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Требует авторизации</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {agents.filter(a => a.status === 'ok' && !a.oauth_ok).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Офлайн</p>
                <p className="text-2xl font-bold text-red-600">
                  {agents.filter(a => a.status !== 'ok').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Детальный статус агентов */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Детальный статус</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {agents.map((agent, index) => (
            <Card key={`${agent.model}-${agent.provider}`} className="transition-all hover:shadow-lg">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getAgentIcon(agent.provider)}
                    <CardTitle className="text-sm font-medium truncate">
                      {agent.provider.replace('_', ' ')}
                    </CardTitle>
                  </div>
                  {getStatusIcon(agent.status, agent.oauth_ok)}
                </div>
              </CardHeader>
              
              <CardContent className="space-y-3">
                {/* Статус подключения */}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Статус:</span>
                  <Badge 
                    variant={agent.status === 'ok' && agent.oauth_ok ? 'default' : 
                            agent.status === 'ok' ? 'secondary' : 'destructive'}
                    className="text-xs"
                  >
                    {agent.status === 'ok' && agent.oauth_ok ? 'ONLINE' :
                     agent.status === 'ok' ? 'AUTH REQUIRED' : 'OFFLINE'}
                  </Badge>
                </div>

                {/* Задержка */}
                {agent.latency_ms && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Задержка:</span>
                    <span className={`text-xs font-mono ${
                      agent.latency_ms < 1000 ? 'text-green-600' : 
                      agent.latency_ms < 3000 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {agent.latency_ms}ms
                    </span>
                  </div>
                )}

                {/* OAuth статус */}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">OAuth:</span>
                  <div className="flex items-center space-x-1">
                    <Wifi className={`h-3 w-3 ${agent.oauth_ok ? 'text-green-500' : 'text-gray-400'}`} />
                    <span className="text-xs">{agent.oauth_ok ? 'Авторизован' : 'Не авторизован'}</span>
                  </div>
                </div>

                {/* Токен метрики */}
                {agent.tokens_used && (
                  <div className="border-t pt-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">Использовано токенов:</span>
                      <span className="text-xs font-bold">{agent.tokens_used.toLocaleString()}</span>
                    </div>
                  </div>
                )}

                {/* CLI путь */}
                {agent.binary_path && (
                  <div className="border-t pt-3">
                    <div className="text-xs text-gray-500 mb-1">CLI путь:</div>
                    <div className="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded truncate">
                      {agent.binary_path}
                    </div>
                  </div>
                )}

                {/* Команда проверки */}
                {agent.probe_command && (
                  <div className="border-t pt-3">
                    <div className="text-xs text-gray-500 mb-1">Проверка:</div>
                    <div className="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded truncate">
                      {agent.probe_command}
                    </div>
                  </div>
                )}

                {/* Ошибки CLI */}
                {agent.cli_error && (
                  <div className="border-t pt-3">
                    <div className="text-xs text-red-600 mb-1">Ошибка CLI:</div>
                    <div className="text-xs font-mono bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded text-red-700 dark:text-red-300 truncate">
                      {agent.cli_error}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Критический статус системы */}
      {(agents.length === 0 || agents.filter(a => a.status === 'ok' && a.oauth_ok).length === 0) && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-600" />
              <CardTitle className="text-red-800 dark:text-red-400">
                Критическое предупреждение системы
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-red-700 dark:text-red-300">
              Обнаружены проблемы с LLM агентами. Система может работать нестабильно.
              Немедленно проверьте конфигурацию OAuth и состояние CLI бинарников.
            </p>
            <div className="mt-4 flex flex-col sm:flex-row gap-2">
              <Button 
                variant="destructive" 
                size="sm"
                onClick={() => window.open('/health/deps', '_blank')}
              >
                <Download className="mr-2 h-4 w-4" />
                Скачать диагностику
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={handleRefresh}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Повторить проверку
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <strong>Ошибка загрузки: </strong>{error}
        </div>
      )}
    </div>
  )
}

export default Agents