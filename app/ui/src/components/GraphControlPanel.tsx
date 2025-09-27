import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import {
  Play,
  Pause,
  Square,
  RotateCcw,
  Timer,
  Activity,
  Settings,
  GitBranch,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  TrendingUp,
  Gauge
} from 'lucide-react'
import { post, get } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { Sparkline } from '@/components/Sparkline'
import { ProgressRing } from '@/components/ProgressRing'

interface Feature {
  id: number
  title: string
  status: string
  priority: number
}

interface GraphRun {
  run_id: string
  feature_id: number
  graph_name?: string
  thread_id?: string
  state_json?: string
  status: string
  last_checkpoint_at: string
  created_at?: string
  updated_at?: string
}

interface Task {
  id: number
  feature_id: number
  role: string
  status: string
  attempts: number
  scheduled_at: string
  started_at?: string
  completed_at?: string
}

interface GraphControlPanelProps {
  feature: Feature
  runs: GraphRun[]
  tasks: Task[]
  onRefresh: () => void
}

interface RunnerMetrics {
  queue_depth: number
  last_tick_ms: number
  active_tasks: number
  completed_today: number
  failed_today: number
}

const GraphControlPanel: React.FC<GraphControlPanelProps> = ({
  feature,
  runs,
  tasks,
  onRefresh
}) => {
  const [loading, setLoading] = useState(false)
  const [metrics, setMetrics] = useState<RunnerMetrics | null>(null)
  const [tickInterval, setTickInterval] = useState<NodeJS.Timeout | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [lastActivity, setLastActivity] = useState<Date>(new Date())

  // Имитация метрик runner'а
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // В реальности это будет GET /api/v1/runner/metrics
        const simulatedMetrics: RunnerMetrics = {
          queue_depth: Math.floor(Math.random() * 10) + 1,
          last_tick_ms: Date.now() - Math.floor(Math.random() * 5000),
          active_tasks: tasks.filter(t => t.status === 'RUNNING').length,
          completed_today: Math.floor(Math.random() * 50) + 10,
          failed_today: Math.floor(Math.random() * 5) + 1
        }
        setMetrics(simulatedMetrics)
      } catch (error) {
        console.error('Failed to fetch runner metrics:', error)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000) // каждые 5 секунд

    return () => clearInterval(interval)
  }, [tasks])

  // Автообновление
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        onRefresh()
        setLastActivity(new Date())
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, onRefresh])

  const currentRun = runs.find(r => r.status === 'RUNNING') || runs[0]

  const handlePlanFeature = async () => {
    try {
      setLoading(true)
      await post(`/orchestrator/features/${feature.id}/plan`)
      onRefresh()
      setLastActivity(new Date())
    } catch (error) {
      console.error('Failed to plan feature:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRunFeature = async () => {
    try {
      setLoading(true)
      await post(`/orchestrator/features/${feature.id}/run`)
      onRefresh()
      setLastActivity(new Date())
    } catch (error) {
      console.error('Failed to run feature:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStopRun = async () => {
    if (!currentRun) return
    try {
      setLoading(true)
      // В реальности: await post(`/orchestrator/runs/${currentRun.run_id}/stop`)
      console.log('Stopping run:', currentRun.run_id)
      onRefresh()
      setLastActivity(new Date())
    } catch (error) {
      console.error('Failed to stop run:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRestartRun = async () => {
    if (!currentRun) return
    try {
      setLoading(true)
      // В реальности: await post(`/orchestrator/runs/${currentRun.run_id}/restart`)
      console.log('Restarting run:', currentRun.run_id)
      onRefresh()
      setLastActivity(new Date())
    } catch (error) {
      console.error('Failed to restart run:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRunnerTick = async () => {
    try {
      setLoading(true)
      await post('/runner/run-once')
      onRefresh()
      setLastActivity(new Date())
    } catch (error) {
      console.error('Failed to trigger runner tick:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return <Play className="h-4 w-4 text-green-600 animate-pulse" />
      case 'DONE':
      case 'COMPLETED':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'FAILED':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'PAUSED':
        return <Pause className="h-4 w-4 text-yellow-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'DONE':
      case 'COMPLETED':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'FAILED':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'PAUSED':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  // Генерируем данные для графиков
  const performanceData = useMemo(() => {
    const data = []
    for (let i = 0; i < 15; i++) {
      data.push(Math.floor(Math.random() * 30) + 20)
    }
    return data
  }, [lastActivity])

  const queueData = useMemo(() => {
    const data = []
    for (let i = 0; i < 10; i++) {
      data.push(Math.floor(Math.random() * 8) + 2)
    }
    return data
  }, [metrics])

  return (
    <div className="space-y-6">

      {/* Статус и основные действия */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <GitBranch className="h-5 w-5" />
              <span>Управление графом</span>
              {autoRefresh && <Badge variant="default" className="text-xs animate-pulse">AUTO</Badge>}
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                size="sm"
                variant={autoRefresh ? 'default' : 'outline'}
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                <Activity className="h-4 w-4 mr-1" />
                Auto
              </Button>
              <Button size="sm" variant="outline" onClick={onRefresh} disabled={loading}>
                <RotateCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* Левая панель - статус фичи */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(feature.status)}
                  <span className="font-medium">Статус фичи</span>
                </div>
                <Badge className={getStatusColor(feature.status)}>
                  {feature.status}
                </Badge>
              </div>

              {currentRun && (
                <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Текущий запуск</span>
                    <Badge variant="outline" className="font-mono text-xs">
                      {currentRun.run_id.slice(-8)}
                    </Badge>
                  </div>
                  <div className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
                    <div>Граф: {currentRun.graph_name || 'неизвестно'}</div>
                    <div>Поток: {currentRun.thread_id}</div>
                    <div>Последний чекпоинт: {formatDate(currentRun.last_checkpoint_at)}</div>
                  </div>
                </div>
              )}

              {metrics && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border text-center">
                    <div className="text-lg font-bold text-blue-600">{metrics.queue_depth}</div>
                    <div className="text-xs text-gray-500">Очередь</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border text-center">
                    <div className="text-lg font-bold text-green-600">{metrics.active_tasks}</div>
                    <div className="text-xs text-gray-500">Активные</div>
                  </div>
                </div>
              )}
            </div>

            {/* Правая панель - действия */}
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <Button
                  onClick={handlePlanFeature}
                  disabled={loading || feature.status !== 'NEW'}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white border-indigo-600 shadow-sm"
                  variant={loading || feature.status !== 'NEW' ? 'outline' : 'default'}
                >
                  <Settings className="h-4 w-4 mr-1" />
                  План
                </Button>

                <Button
                  onClick={handleRunFeature}
                  disabled={loading || !['PLANNED', 'NEW'].includes(feature.status)}
                  className="w-full bg-green-600 hover:bg-green-700 text-white shadow-sm"
                  variant="default"
                >
                  <Play className="h-4 w-4 mr-1" />
                  Старт
                </Button>

                <Button
                  onClick={handleStopRun}
                  disabled={loading || !currentRun || currentRun.status !== 'RUNNING'}
                  className="w-full bg-red-600 hover:bg-red-700 text-white shadow-sm"
                  variant="destructive"
                >
                  <Square className="h-4 w-4 mr-1" />
                  Стоп
                </Button>

                <Button
                  onClick={handleRestartRun}
                  disabled={loading || !currentRun}
                  className="w-full bg-orange-600 hover:bg-orange-700 text-white border-orange-600 shadow-sm"
                  variant={loading || !currentRun ? 'outline' : 'default'}
                >
                  <RotateCcw className="h-4 w-4 mr-1" />
                  Рестарт
                </Button>
              </div>

              <Button
                onClick={handleRunnerTick}
                disabled={loading}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white border-purple-600 shadow-sm"
                variant={loading ? 'outline' : 'default'}
              >
                <Timer className="h-4 w-4 mr-1" />
                Тик Runner
              </Button>

              <div className="text-xs text-gray-500 text-center">
                Последняя активность: {formatDate(lastActivity.toISOString())}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Метрики и мониторинг */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Производительность */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <TrendingUp className="h-4 w-4" />
              <span>Производительность</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-blue-600">
                  {metrics?.completed_today || 0}
                </span>
                <Badge variant="secondary">сегодня</Badge>
              </div>
              <div className="text-sm text-gray-600">Задач выполнено</div>
              <Sparkline
                data={performanceData}
                width={120}
                height={30}
                color="#3B82F6"
                animate={true}
              />
            </div>
          </CardContent>
        </Card>

        {/* Ошибки */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4" />
              <span>Ошибки</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-red-600">
                  {metrics?.failed_today || 0}
                </span>
                <Badge variant="destructive">критично</Badge>
              </div>
              <div className="text-sm text-gray-600">Провалов сегодня</div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-red-500 h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${metrics ? Math.min((metrics.failed_today / (metrics.completed_today + metrics.failed_today)) * 100, 100) : 0}%`
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Очередь */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Очередь</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-purple-600">
                  {metrics?.queue_depth || 0}
                </span>
                <Badge variant="outline">ожидают</Badge>
              </div>
              <div className="text-sm text-gray-600">Задач в очереди</div>
              <Sparkline
                data={queueData}
                width={120}
                height={30}
                color="#7C3AED"
                animate={true}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Прогресс выполнения */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center space-x-2">
            <Gauge className="h-4 w-4" />
            <span>Общий прогресс фичи</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-6">
            <ProgressRing
              value={tasks.filter(t => t.status === 'DONE').length}
              max={Math.max(tasks.length, 1)}
              size={80}
              strokeWidth={6}
              gradientFrom="#10B981"
              gradientTo="#059669"
            />
            <div className="flex-1 space-y-3">
              {['DONE', 'RUNNING', 'FAILED', 'NEW'].map(status => {
                const count = tasks.filter(t => t.status === status).length
                const percentage = tasks.length > 0 ? (count / tasks.length) * 100 : 0
                return (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(status)}
                      <span className="text-sm font-medium">{status}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${
                            status === 'DONE' ? 'bg-green-500' :
                            status === 'RUNNING' ? 'bg-blue-500' :
                            status === 'FAILED' ? 'bg-red-500' : 'bg-gray-400'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600 w-8">{count}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default GraphControlPanel