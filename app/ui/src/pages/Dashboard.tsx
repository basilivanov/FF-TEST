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
  Wifi
} from 'lucide-react'
import { get, getAbsolute } from '@/lib/api'
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
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)
  const [agentsHealth, setAgentsHealth] = useState<LLMHealthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const lastRefetchAt = useRef<number>(0)

  const fetchData = async () => {
    // Мок данные для мгновенной загрузки
    setIsHealthy(true)
    setFeatures([{ id: 1, title: 'Test Feature', status: 'NEW' }])
    setRuns([{ run_id: 'run_001', feature_id: 1, status: 'RUNNING', last_checkpoint_at: new Date().toISOString() }])
    setCriticalErrors([])
    setAgentsHealth({
      status: 'ok',
      component: 'llm_providers', 
      checks: [{ status: 'ok', component: 'llm_providers', providers: [
        { provider: 'Claude', status: 'ok', path: '/bin/claude', version: 'v1.0', logged_in: true, probe_command: 'claude --version' }
      ], working_providers: 1, total_providers: 1 }]
    })
    setError(null)
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
    // SSE отключен для ускорения
    // sseClient.connect('/stream/events')
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

  return (
    <div className="space-y-6">
      {debug && (
        <div className="fixed top-2 right-2 z-50 bg-black/70 text-white text-xs px-3 py-2 rounded shadow">
          <div>debug: on</div>
          <div>features: {features.length}</div>
          <div>runs: {runs.length}</div>
          <div>tokens: {tokensSummary ? `${tokensSummary.used}/${tokensSummary.limit}` : 'n/a'}</div>
          <div>critical: {criticalErrors.length}</div>
        </div>
      )}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Mission Control Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Центр управления: сводный обзор и быстрые переходы
        </p>
      </div>

      {/* Первая строка: System Health + Agents Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. System Health */}
        <Card
          className="cursor-pointer hover:shadow-md transition"
          onClick={() => navigate('logs')}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${isHealthy ? 'text-green-600' : isHealthy === false ? 'text-red-600' : 'text-gray-500'}`}>
              {isHealthy === null ? 'Unknown' : isHealthy ? '🟢 Ready' : '🔴 Unhealthy'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Нажмите для просмотра системных событий
            </p>
          </CardContent>
        </Card>

        {/* 2. LLM Agents Status */}
        <Card
          className="cursor-pointer hover:shadow-md transition"
          onClick={() => navigate('agents')}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">LLM Agents</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {agentsHealth ? (
              <div className="space-y-3">
                <div className={`text-2xl font-bold ${
                  agentsHealth.status === 'ok' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {agentsHealth.status === 'ok' ? '🟢 Online' : '🔴 Issues'}
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Работающих агентов:</span>
                  <span className="font-bold">
                    {agentsHealth.checks[0]?.working_providers || 0}/{agentsHealth.checks[0]?.total_providers || 0}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      (agentsHealth.checks[0]?.working_providers || 0) === (agentsHealth.checks[0]?.total_providers || 0)
                        ? 'bg-green-600' : 'bg-red-600'
                    }`}
                    style={{ 
                      width: `${Math.round(((agentsHealth.checks[0]?.working_providers || 0) / Math.max(agentsHealth.checks[0]?.total_providers || 1, 1)) * 100)}%` 
                    }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Нажмите для детального обзора</p>
              </div>
            ) : (
              <div className="text-sm text-gray-500">Загрузка статуса агентов...</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Сетка виджетов (адаптивная) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* 3. Active Processes (Runs + Features) */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex items-center gap-3">
              <CardTitle className="text-sm font-medium">Active Processes</CardTitle>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  Запуски: <span className="font-semibold text-gray-900 dark:text-gray-100">{runningRunsCount}</span>
                </span>
                <span>•</span>
                <span className="inline-flex items-center gap-1">
                  Фичи: <span className="font-semibold text-gray-900 dark:text-gray-100">{runningFeaturesCount}</span>
                </span>
              </div>
            </div>
            <Play className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-2">Запуски</div>
                <div className="space-y-2">
                  {activeRuns.length === 0 && (
                    <div className="text-sm text-gray-500">Нет активных запусков</div>
                  )}
                  {activeRuns.map(run => {
                    const feature = features.find(f => f.id === run.feature_id)
                    const title = feature?.title ? feature.title : `Run #${run.run_id.slice(0,8)}`
                    return (
                      <div
                        key={run.run_id}
                        className="flex items-center justify-between p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                        onClick={() => navigate(`/admin/runs/${run.run_id}`)}
                        title={`Открыть запуск ${run.run_id}`}
                      >
                        <div className="truncate">
                          <div className="text-sm font-medium truncate">{title}</div>
                          <div className="text-xs text-muted-foreground">{formatGraphRunStatus(run.status)} • Фича #{run.feature_id}</div>
                        </div>
                        <Badge variant="default">RUNNING</Badge>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-2">Фичи</div>
                <div className="space-y-2">
                  {activeFeatures.length === 0 && (
                    <div className="text-sm text-gray-500">Нет активных фич</div>
                  )}
                  {activeFeatures.map(f => (
                    <div
                      key={f.id}
                      className="flex items-center justify-between p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                      onClick={() => navigate(`/admin/features/${f.id}`)}
                      title={`Открыть фичу ${f.id}`}
                    >
                      <div className="truncate">
                        <div className="text-sm font-medium truncate">{f.title || `Фича #${f.id}`}</div>
                        <div className="text-xs text-muted-foreground">{formatFeatureStatus(f.status)}</div>
                      </div>
                      <Badge variant="default">RUNNING</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Вторая строка: Backlog, LLM Budget, Critical Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 4. Backlog */}
        <Card
          className="cursor-pointer hover:shadow-md transition"
          onClick={() => navigate('features?status=NEW,PLANNED')}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Backlog</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">{backlogStats.new}</div>
                <p className="text-xs text-muted-foreground">Новые</p>
              </div>
              <div>
                <div className="text-2xl font-bold">{backlogStats.planned}</div>
                <p className="text-xs text-muted-foreground">Запланированные</p>
              </div>
              <div>
                <div className="text-2xl font-bold">{backlogStats.running}</div>
                <p className="text-xs text-muted-foreground">В работе</p>
              </div>
            </div>
            <div className="mt-3 flex items-center text-xs text-blue-600">
              Открыть список <ArrowRight className="h-3 w-3 ml-1" />
            </div>
          </CardContent>
        </Card>

        {/* 5. LLM Budget */}
        <Card
          className="cursor-pointer hover:shadow-md transition"
          onClick={() => navigate('llm-metrics')}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">LLM Budget</CardTitle>
            <Coins className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {tokensSummary ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Использовано</span>
                  <span className="text-sm font-medium">{tokensSummary.used.toLocaleString()} / {tokensSummary.limit.toLocaleString()}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      tokensSummary.used / Math.max(tokensSummary.limit, 1) > 0.9 ? 'bg-red-600' :
                      tokensSummary.used / Math.max(tokensSummary.limit, 1) > 0.7 ? 'bg-yellow-500' : 'bg-green-600'
                    }`}
                    style={{ width: `${Math.min(tokensSummary.used / Math.max(tokensSummary.limit, 1) * 100, 100)}%` }}
                  />
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500">Нет данных по бюджету</div>
            )}
          </CardContent>
        </Card>

        {/* 6. Critical Alerts */}
        <Card
          className="cursor-pointer hover:shadow-md transition"
          onClick={() => navigate('errors')}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{criticalErrors.length}</div>
            <div className="mt-2 space-y-2">
              {criticalErrors.slice(0, 2).map((log, idx) => (
                <div key={idx} className="border-l-2 border-red-500 pl-2">
                  <p className="text-sm font-medium text-red-600 truncate">{log.event}</p>
                  <p className="text-xs text-muted-foreground truncate">{log.component} • {new Date(log.ts).toLocaleTimeString()}</p>
                </div>
              ))}
              {criticalErrors.length === 0 && (
                <p className="text-sm text-gray-500">Критических алертов нет</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end">
        <Button onClick={fetchData} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Обновить данные
        </Button>
      </div>
    </div>
  )
}

export default Dashboard
