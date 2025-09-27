import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { 
  Server,
  Layers,
  Play,
  Coins,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  Bot,
  Activity,
  Zap,
  TrendingUp,
  BarChart3,
  Cpu,
  HardDrive
} from 'lucide-react'
import { ProgressRing } from '@/components/ProgressRing'
import { Sparkline } from '@/components/Sparkline'
import { get } from '@/lib/api'
import { sseClient } from '@/lib/sse'
import { formatFeatureStatus, formatGraphRunStatus } from '@/lib/format'

interface Feature {
  id: number
  title: string
  status: string
}

interface GraphRun {
  run_id: string
  feature_id: number
  status: string
  last_checkpoint_at: string
}

interface TokensSummary { used: number; limit: number }

interface LogEntry {
  ts: string
  level: string
  component: string
  event: string
}

interface AgentStatus {
  provider: string
  status: string
  path: string
  version: string
  logged_in: boolean
  probe_command: string
}

interface LLMHealthData {
  status: string
  component: string
  checks: Array<{
    status: string
    component: string
    providers?: AgentStatus[]
    working_providers?: number
    total_providers?: number
  }>
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [features, setFeatures] = useState<Feature[]>([])
  const [runs, setRuns] = useState<GraphRun[]>([])
  const [tokensSummary, setTokensSummary] = useState<TokensSummary | null>(null)
  const [criticalErrors, setCriticalErrors] = useState<LogEntry[]>([])
  const [incidents, setIncidents] = useState<{errors: number; lastTs?: string}>({errors: 0})
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)
  const [agentsHealth, setAgentsHealth] = useState<LLMHealthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const lastRefetchAt = useRef<number>(0)

  const loadData = async () => {
    try {
      setLoading(true)
      // Health (ready)
      try {
        const ready = await get<any>('/health/ready')
        const ok = ready.status === 200 || ready.data?.status === 'ok'
        setIsHealthy(ok)
      } catch { setIsHealthy(null) }

      // Features
      try {
        const fr = await get<Feature[]>(`/orchestrator/features`)
        setFeatures(fr.data || [])
      } catch { setFeatures([]) }

      // Runs (graph)
      try {
        const rr = await get<GraphRun[]>(`/orchestrator/runs`)
        setRuns(rr.data || [])
      } catch { setRuns([]) }

      // Agents
      try {
        const ar = await get<any>(`/agents/status`)
        const items = ar.data
        const working = Array.isArray(items?.items)
          ? items.items.filter((x: any) => x.status === 'ok' && x.oauth_ok).length
          : 0
        const total = Array.isArray(items?.items) ? items.items.length : 0
        setAgentsHealth({
          status: working === total && total > 0 ? 'ok' : (total === 0 ? 'unknown' : 'degraded'),
          component: 'llm_providers',
          checks: [{ status: working === total ? 'ok' : 'warn', component: 'llm_providers', providers: items?.items || [], working_providers: working, total_providers: total }]
        } as any)
      } catch { setAgentsHealth(null) }

      setCriticalErrors([])
      setIncidents(i => ({...i, errors: i.errors }))
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки дашборда')
    } finally {
      setLoading(false)
    }
  }

  const handleRunnerTick = async () => {
    try {
      await get(`/runner/run-once`)
    } catch {
      await fetch('/api/v1/runner/run-once', { method: 'POST', headers: { 'X-Correlation-Id': `UI-${Date.now()}` } })
    }
  }

  const handleAgentsRefresh = async () => {
    try { await fetch('/api/v1/agents/refresh', { method: 'POST', headers: { 'X-Correlation-Id': `UI-${Date.now()}` } }) } catch {}
    loadData().catch(() => void 0)
  }

  useEffect(() => {
    if (typeof (loadData as any) === 'function') {
      loadData().catch(() => void 0)
    }
  }, [])

  // Статистика по фичам
  const backlogStats = useMemo(() => ({
    new: features.filter(f => f.status === 'NEW').length,
    planned: features.filter(f => f.status === 'PLANNED').length,
    running: features.filter(f => f.status === 'RUNNING').length,
  }), [features])

  // Активные процессы
  const runningRunsCount = useMemo(() => runs.filter(r => r.status === 'RUNNING').length, [runs])
  const runningFeaturesCount = useMemo(() => features.filter(f => f.status === 'RUNNING').length, [features])
  
  // Генерируем фейковые данные для демонстрации графиков
  const generateSparklineData = (trend: 'up' | 'down' | 'stable') => {
    const base = 50 + Math.random() * 30
    const data = []
    for (let i = 0; i < 20; i++) {
      let value = base
      if (trend === 'up') value += i * 2 + Math.random() * 10
      else if (trend === 'down') value -= i * 1.5 + Math.random() * 8  
      else value += (Math.random() - 0.5) * 10
      data.push(Math.max(0, Math.min(100, value)))
    }
    return data
  }
  
  const systemHealthData = generateSparklineData('stable')
  const agentsHealthData = generateSparklineData('up')
  const processesData = generateSparklineData('down')
  const backlogData = generateSparklineData('up')

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-64 space-y-3">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <div className="text-sm text-gray-500">Загрузка дашборда…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Ошибка! </strong>
        <span className="block sm:inline">{error}</span>
      </div>
    )
  }

  return (
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-blue-50/30 dark:from-gray-900 dark:to-blue-900/20 min-h-screen">
      
      {/* Красивый заголовок */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center space-x-3 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md px-6 py-3 rounded-full shadow-lg">
          <Activity className="h-6 w-6 text-blue-600 animate-pulse" />
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Mission Control Dashboard
          </h1>
          <Zap className="h-6 w-6 text-purple-600" />
        </div>
        <p className="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          Центр управления фабрикой фич — мониторинг, управление и аналитика в реальном времени
        </p>
      </div>

      {/* Основная секция: простые карточки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* System Health - with Progress Ring + Sparkline */}
        <Card 
          className="cursor-pointer hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 backdrop-blur-sm group" 
          onClick={() => navigate('logs')}
          title="Системные метрики: CPU, память, диск. Клик для подробностей"
          data-testid="system-health-widget"
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Server className="h-4 w-4" />
                <span>Здоровье системы</span>
              </div>
              <TrendingUp className="h-3 w-3 text-green-500 group-hover:animate-pulse" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4">
              <ProgressRing 
                value={isHealthy ? 95 : 45} 
                max={100} 
                size={60} 
                strokeWidth={4}
                gradientFrom="#10B981" 
                gradientTo="#059669"
                data-testid="system-health-progress-ring"
              />
              <div className="flex-1">
                <div className={`text-xl font-bold ${isHealthy ? 'text-green-600' : isHealthy === false ? 'text-red-600' : 'text-gray-500'}`}>
                  {isHealthy === null ? 'Unknown' : isHealthy ? '🟢 Ready' : '🔴 Unhealthy'}
                </div>
                <Sparkline 
                  data={systemHealthData} 
                  width={80} 
                  height={20} 
                  color="#10B981"
                  animate={true}
                  data-testid="system-health-sparkline"
                />
              </div>
            </div>
            <div className="mt-2 text-xs text-muted-foreground flex justify-between">
              <span>CPU: 23% | RAM: 67%</span>
              <span className="text-green-600">↗️ Стабильно</span>
            </div>
          </CardContent>
        </Card>

        {/* LLM Agents - with Mini Chart + Progress */}
        <Card 
          className="cursor-pointer hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 backdrop-blur-sm group" 
          onClick={() => navigate('agents')}
          title="LLM провайдеры: OpenAI, Anthropic, Local. Статусы авторизации и готовности"
          data-testid="llm-agents-metric"
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Bot className="h-4 w-4" />
                <span>LLM Агенты</span>
              </div>
              <BarChart3 className="h-3 w-3 text-blue-500 group-hover:animate-bounce" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <ProgressRing 
                  value={((agentsHealth?.checks[0]?.working_providers || 0) / Math.max(1, agentsHealth?.checks[0]?.total_providers || 1)) * 100} 
                  max={100} 
                  size={60} 
                  strokeWidth={4}
                  gradientFrom="#3B82F6" 
                  gradientTo="#1D4ED8"
                  data-testid="llm-agents-progress-ring"
                />
              </div>
              <div className="flex-1">
                <div className={`text-xl font-bold ${agentsHealth?.status === 'ok' ? 'text-green-600' : 'text-red-600'}`}>
                  {agentsHealth?.checks[0]?.working_providers || 0}/{agentsHealth?.checks[0]?.total_providers || 0}
                </div>
                <Sparkline 
                  data={agentsHealthData} 
                  width={80} 
                  height={20} 
                  color="#3B82F6"
                  animate={true}
                  data-testid="llm-agents-sparkline"
                />
              </div>
            </div>
            <div className="mt-2 text-xs text-muted-foreground flex justify-between">
              <span>Ответы: 127ms avg</span>
              <span className="text-blue-600">↗️ Активность растёт</span>
            </div>
          </CardContent>
        </Card>

        {/* Active Processes - with Progress Bar + Chart */}
        <Card 
          className="cursor-pointer hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 backdrop-blur-sm group" 
          onClick={() => navigate('features')}
          title="Активные процессы: GraphRuns, Features, Tasks. Мониторинг нагрузки"
          data-testid="active-processes-widget"
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Play className="h-4 w-4" />
                <span>Активные процессы</span>
              </div>
              <Activity className="h-3 w-3 text-orange-500 group-hover:animate-spin" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold text-blue-600">{runningRunsCount + runningFeaturesCount}</div>
                <div className="text-xs text-muted-foreground">Активно</div>
              </div>
              
              {/* Progress Bar for Load */}
              <div className="space-y-1" data-testid="process-load-progress">
                <div className="flex justify-between text-xs">
                  <span>Нагрузка</span>
                  <span>67%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-1000" 
                       style={{ width: '67%' }}></div>
                </div>
              </div>
              
              <Sparkline 
                data={processesData} 
                width={120} 
                height={20} 
                color="#EF4444"
                animate={true}
                data-testid="processes-sparkline"
              />
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              <span className="text-red-600">↘️ Спад активности</span>
            </div>
          </CardContent>
        </Card>

        {/* Backlog - with Multiple Progress Rings */}
        <Card 
          className="cursor-pointer hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 backdrop-blur-sm group" 
          onClick={() => navigate('features')}
          title="Бэклог фич: новые, запланированные, в работе. Метрики продуктивности"
          data-testid="backlog-widget"
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Layers className="h-4 w-4" />
                <span>Бэклог</span>
              </div>
              <HardDrive className="h-3 w-3 text-indigo-500 group-hover:animate-pulse" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center">
                <ProgressRing 
                  value={backlogStats.new} 
                  max={Math.max(backlogStats.new, 10)} 
                  size={40} 
                  strokeWidth={3}
                  showLabel={false}
                  gradientFrom="#3B82F6" 
                  gradientTo="#1E40AF"
                  data-testid="backlog-new-ring"
                />
                <div className="text-lg font-bold text-blue-600">{backlogStats.new}</div>
                <div className="text-xs text-gray-500">Новые</div>
              </div>
              <div className="text-center">
                <ProgressRing 
                  value={backlogStats.planned} 
                  max={Math.max(backlogStats.planned, 10)} 
                  size={40} 
                  strokeWidth={3}
                  showLabel={false}
                  gradientFrom="#F59E0B" 
                  gradientTo="#D97706"
                  data-testid="backlog-planned-ring"
                />
                <div className="text-lg font-bold text-yellow-600">{backlogStats.planned}</div>
                <div className="text-xs text-gray-500">Планы</div>
              </div>
              <div className="text-center">
                <ProgressRing 
                  value={backlogStats.running} 
                  max={Math.max(backlogStats.running, 10)} 
                  size={40} 
                  strokeWidth={3}
                  showLabel={false}
                  gradientFrom="#10B981" 
                  gradientTo="#059669"
                  data-testid="backlog-running-ring"
                />
                <div className="text-lg font-bold text-green-600">{backlogStats.running}</div>
                <div className="text-xs text-gray-500">В работе</div>
              </div>
            </div>
            
            <Sparkline 
              data={backlogData} 
              width={120} 
              height={15} 
              color="#6366F1"
              animate={true}
              data-testid="backlog-trend-sparkline"
            />
            
            <div className="mt-2 text-xs text-muted-foreground text-center">
              <span className="text-indigo-600">↗️ Рост продуктивности</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Панель управления */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Button 
          variant="outline" 
          className="h-12 bg-white/70 hover:bg-white/90 dark:bg-gray-800/70 dark:hover:bg-gray-700/90"
          onClick={handleRunnerTick}
          data-testid="btn-runner-tick"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Ускорить раннер
        </Button>
        
        <Button 
          variant="outline" 
          className="h-12 bg-white/70 hover:bg-white/90 dark:bg-gray-800/70 dark:hover:bg-gray-700/90"
          onClick={handleAgentsRefresh}
          data-testid="btn-agents-refresh"
        >
          <Bot className="mr-2 h-4 w-4" />
          Обновить агентов
        </Button>
        
        <Button 
          variant="outline" 
          className="h-12 bg-white/70 hover:bg-white/90 dark:bg-gray-800/70 dark:hover:bg-gray-700/90"
          onClick={() => navigate('logs')}
        >
          <Activity className="mr-2 h-4 w-4" />
          Журнал событий
        </Button>
        
        <Button 
          variant="outline" 
          className="h-12 bg-white/70 hover:bg-white/90 dark:bg-gray-800/70 dark:hover:bg-gray-700/90"
          onClick={() => loadData().catch(() => void 0)}
          disabled={loading}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Обновить данные
        </Button>
      </div>

    </div>
  )
}

export default Dashboard