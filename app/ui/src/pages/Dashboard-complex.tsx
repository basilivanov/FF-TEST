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
  Shield,
  Cpu,
  Wifi,
  TrendingUp,
  Activity,
  Zap
} from 'lucide-react'
import { get } from '@/lib/api'
import { sseClient } from '@/lib/sse'
import { formatFeatureStatus, formatGraphRunStatus } from '@/lib/format'
import { GlassCard } from '@/components/GlassCard'
import { MetricCard } from '@/components/MetricCard'
import { SystemHealthRadial } from '@/components/SystemHealthRadial'
import { ProgressRing } from '@/components/ProgressRing'
import { Sparkline } from '@/components/Sparkline'
import { generateSparklineData, getStatusFromValue, formatNumber } from '@/lib/utils'

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
  
  // Данные для красивых визуализаций
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: generateSparklineData(20, 10, 80),
    memory: generateSparklineData(20, 30, 90), 
    network: generateSparklineData(20, 5, 95),
    database: generateSparklineData(20, 20, 75)
  })

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

      // Critical alerts — заполним позже из SSE/логов; пока пусто
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
      await get(`/runner/run-once`) // POST would be more correct, but our helper defaults to GET; use fetch below
    } catch {
      // fallback to POST explicitly
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
    // Реал-тайм: подключаем SSE для инцидентов и прогресса
    // Поддерживаем простую агрегацию ошибок без избыточного рендера
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    (async () => {
      try {
        const detach: Array<() => void> = []
        sseClient.connect('/stream/events')
        // Слушаем только критичные события и ошибки
        detach.push(sseClient.onEvent('error', (_type, data) => {
          try {
            const ts = typeof data?.timestamp === 'number' ? new Date(data.timestamp * 1000).toISOString() : (data?.timestamp || new Date().toISOString())
            const entry: LogEntry = {
              ts,
              level: 'ERROR',
              component: 'pipeline',
              event: data?.error || 'Unknown error'
            }
            // До 10 последних
            setCriticalErrors(prev => [entry, ...prev].slice(0, 10))
            setIncidents(prev => ({ errors: Math.min(prev.errors + 1, 999), lastTs: ts }))
          } catch { /* ignore */ }
        }))
        // job_* события → мягкий рефетч не чаще раза в 2с
        const maybeRefetch = () => {
          const now = Date.now()
          if (!lastRefetchAt.current || (now - lastRefetchAt.current) > 2000) {
            lastRefetchAt.current = now
            loadData().catch(() => void 0)
          }
        }
        detach.push(sseClient.onEvent('job_started', () => maybeRefetch()))
        detach.push(sseClient.onEvent('job_finished', () => maybeRefetch()))
        return () => { detach.forEach(off => off()) }
      } catch {
        // ignore
      }
    })()
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
  const activeRuns = useMemo(() => runs.filter(r => r.status === 'RUNNING').slice(0, 3), [runs])
  const activeFeatures = useMemo(() => features.filter(f => f.status === 'RUNNING').slice(0, 3), [features])

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

  const debug = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('debug') === '1'

  // Мемоизированные метрики для красивых визуализаций
  const healthMetrics = useMemo(() => [
    { name: 'API', value: isHealthy ? 95 : 30, max: 100, status: isHealthy ? 'healthy' : 'critical' as const },
    { name: 'Агенты', value: ((agentsHealth?.checks[0]?.working_providers || 0) / Math.max(agentsHealth?.checks[0]?.total_providers || 1, 1)) * 100, max: 100, status: agentsHealth?.status === 'ok' ? 'healthy' : 'warning' as const },
    { name: 'База', value: 88, max: 100, status: 'healthy' as const },
    { name: 'Память', value: 72, max: 100, status: 'warning' as const }
  ], [isHealthy, agentsHealth])

  const overallHealthScore = useMemo(() => {
    return Math.round(healthMetrics.reduce((acc, metric) => acc + metric.value, 0) / healthMetrics.length)
  }, [healthMetrics])

  return (
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-blue-50/30 dark:from-gray-900 dark:to-blue-900/20 min-h-screen">
      {debug && (
        <div className="fixed top-2 right-2 z-50 bg-black/70 backdrop-blur-md text-white text-xs px-3 py-2 rounded shadow-lg">
          <div>debug: on</div>
          <div>features: {features.length}</div>
          <div>runs: {runs.length}</div>
          <div>tokens: {tokensSummary ? `${tokensSummary.used}/${tokensSummary.limit}` : 'n/a'}</div>
          <div>critical: {criticalErrors.length}</div>
        </div>
      )}
      
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

      {/* Главная секция: Здоровье системы */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Радиальная диаграмма здоровья системы */}
        <div className="xl:col-span-1">
          <GlassCard variant="glass" className="p-6 text-center">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-semibold text-gray-800 dark:text-white flex items-center justify-center space-x-2">
                <Server className="h-5 w-5" />
                <span>Здоровье системы</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SystemHealthRadial 
                metrics={healthMetrics}
                overallHealth={overallHealthScore}
                data-testid="system-health-widget"
              />
            </CardContent>
          </GlassCard>
        </div>

        {/* Метрики производительности */}
        <div className="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
          <MetricCard
            title="LLM Агенты"
            value={`${agentsHealth?.checks[0]?.working_providers || 0}/${agentsHealth?.checks[0]?.total_providers || 0}`}
            subtitle="Активных агентов"
            icon={Bot}
            trend={systemMetrics.cpu}
            progress={{
              value: agentsHealth?.checks[0]?.working_providers || 0,
              max: agentsHealth?.checks[0]?.total_providers || 1,
              label: 'Онлайн'
            }}
            status={agentsHealth?.status === 'ok' ? 'success' : 'warning'}
            variant="glass"
            onClick={() => navigate('agents')}
            data-testid="llm-agents-metric"
          />

          <MetricCard
            title="Активные процессы"
            value={runningRunsCount + runningFeaturesCount}
            subtitle="Запуски + Фичи"
            icon={Play}
            trend={systemMetrics.network}
            progress={{
              value: runningRunsCount,
              max: Math.max(runningRunsCount + 5, 10),
              label: 'Загрузка'
            }}
            status="success"
            variant="glass"
            onClick={() => navigate('features')}
            data-testid="active-processes-metric"
          />

          <MetricCard
            title="Бюджет токенов"
            value={tokensSummary ? `${formatNumber(tokensSummary.used)}` : '0'}
            subtitle={tokensSummary ? `из ${formatNumber(tokensSummary.limit)}` : 'Нет данных'}
            icon={Coins}
            trend={systemMetrics.memory}
            progress={tokensSummary ? {
              value: tokensSummary.used,
              max: tokensSummary.limit,
              label: 'Использовано'
            } : undefined}
            status={tokensSummary && tokensSummary.used / tokensSummary.limit > 0.8 ? 'warning' : 'success'}
            variant="glass"
            onClick={() => navigate('tokens')}
            data-testid="token-budget-metric"
          />

          <MetricCard
            title="Критические события"
            value={criticalErrors.length}
            subtitle="За последний час"
            icon={AlertTriangle}
            trend={systemMetrics.database}
            status={criticalErrors.length > 5 ? 'error' : criticalErrors.length > 0 ? 'warning' : 'success'}
            variant="glass"
            onClick={() => navigate('errors')}
            data-testid="critical-events-metric"
          >
            {criticalErrors.length > 0 && (
              <div className="mt-3 space-y-2">
                {criticalErrors.slice(0, 2).map((log, idx) => (
                  <div key={idx} className="text-left p-2 bg-red-50 dark:bg-red-900/20 rounded border-l-2 border-red-500">
                    <p className="text-xs font-medium text-red-700 dark:text-red-300 truncate">{log.event}</p>
                    <p className="text-xs text-red-600 dark:text-red-400">{new Date(log.ts).toLocaleTimeString()}</p>
                  </div>
                ))}
              </div>
            )}
          </MetricCard>
        </div>
      </div>

      {/* Секция активности и производительности */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Backlog и очередь */}
        <GlassCard variant="gradient" className="p-6">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-gray-800 dark:text-white flex items-center space-x-2">
              <Layers className="h-5 w-5" />
              <span>Бэклог и очередь</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{backlogStats.new}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Новые</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600">{backlogStats.planned}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Запланированные</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{backlogStats.running}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">В работе</div>
              </div>
            </div>
            
            {/* Спарклайн тренда активности */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Активность за день</span>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
              <Sparkline 
                data={generateSparklineData(24, 2, 15)}
                width={280}
                height={50}
                color="#3B82F6"
                showDots={true}
                data-testid="activity-sparkline"
              />
            </div>
            
            <Button 
              variant="outline" 
              className="w-full mt-4 bg-white/50 hover:bg-white/70"
              onClick={() => navigate('features')}
            >
              Открыть все фичи <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </GlassCard>

        {/* Активные процессы */}
        <GlassCard variant="glass" className="p-6">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-gray-800 dark:text-white flex items-center space-x-2">
              <Play className="h-5 w-5" />
              <span>Активные процессы</span>
              <Badge variant="default" className="ml-auto">
                {runningRunsCount + runningFeaturesCount}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Запуски */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Запуски</span>
                  <span className="text-sm text-blue-600 font-semibold">{runningRunsCount}</span>
                </div>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {activeRuns.length === 0 ? (
                    <div className="text-sm text-gray-500 text-center py-2">Нет активных запусков</div>
                  ) : (
                    activeRuns.map((run, idx) => {
                      const feature = features.find(f => f.id === run.feature_id)
                      return (
                        <div
                          key={run.run_id}
                          className="flex items-center justify-between p-2 rounded-lg bg-white/50 dark:bg-gray-800/50 hover:bg-white/70 dark:hover:bg-gray-700/70 cursor-pointer transition-all"
                          onClick={() => navigate(`/runs/${run.run_id}`)}
                        >
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                            <span className="text-sm font-medium truncate">
                              {feature?.title || `Run #${run.run_id.slice(0,8)}`}
                            </span>
                          </div>
                          <Badge variant="outline" className="text-xs">RUNNING</Badge>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>

              {/* Фичи */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Фичи</span>
                  <span className="text-sm text-green-600 font-semibold">{runningFeaturesCount}</span>
                </div>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {activeFeatures.length === 0 ? (
                    <div className="text-sm text-gray-500 text-center py-2">Нет активных фич</div>
                  ) : (
                    activeFeatures.map((feature, idx) => (
                      <div
                        key={feature.id}
                        className="flex items-center justify-between p-2 rounded-lg bg-white/50 dark:bg-gray-800/50 hover:bg-white/70 dark:hover:bg-gray-700/70 cursor-pointer transition-all"
                        onClick={() => navigate(`/features/${feature.id}`)}
                      >
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                          <span className="text-sm font-medium truncate">
                            {feature.title || `Фича #${feature.id}`}
                          </span>
                        </div>
                        <Badge variant="outline" className="text-xs">RUNNING</Badge>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </GlassCard>
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
