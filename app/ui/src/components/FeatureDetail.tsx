import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import {
  Library,
  Play,
  Calendar,
  User,
  Layers,
  CheckCircle,
  Clock,
  XCircle,
  RotateCcw,
  Link2,
  AlertTriangle,
  GitBranch,
  Target,
  Activity,
  BarChart3,
  Settings,
  ArrowLeft,
  ExternalLink,
  TestTube
} from 'lucide-react'
import { get, post } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { Link, useParams } from 'react-router-dom'
import FeatureFlightMap from '@/components/FeatureFlightMap'
import FeatureTimeline from '@/components/FeatureTimeline'
import GraphControlPanel from '@/components/GraphControlPanel'
import { Sparkline } from '@/components/Sparkline'
import { ProgressRing } from '@/components/ProgressRing'

interface Feature {
  id: number
  title: string
  intent_json: any
  status: string
  priority: number
  created_at: string
  created_by: string
  env: string
}

interface Task {
  id: number
  feature_id: number
  role: string
  status: string
  attempts: number
  scheduled_at: string
  started_at?: string
}

interface GraphRun {
  run_id: string
  feature_id: number
  graph_name?: string
  thread_id?: string
  state_json?: string
  status: string
  last_checkpoint_at: string
}

interface FeatureDetailProps {
  onRefresh?: () => void
}

const FeatureDetail: React.FC<FeatureDetailProps> = ({ onRefresh }) => {
  const { id } = useParams<{ id: string }>()
  const [feature, setFeature] = useState<Feature | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [runs, setRuns] = useState<GraphRun[]>([])
  const [artifacts, setArtifacts] = useState<any | null>(null)
  const [qaReport, setQaReport] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [planning, setPlanning] = useState(false)
  const [running, setRunning] = useState(false)

  const lastRun = useMemo(() => runs && runs.length ? runs[0] : null, [runs])
  const watchdog = useMemo(() => {
    try {
      const raw = lastRun?.state_json
      if (!raw) return null
      const obj = typeof raw === 'string' ? JSON.parse(raw) : raw
      return {
        decision: obj?.watchdog_decision || 'CONTINUE',
        context: obj?.escalation_context || '',
        failuresCount: Array.isArray(obj?.watchdog_failures) ? obj.watchdog_failures.length : 0
      }
    } catch { return null }
  }, [lastRun])

  const fetchData = async () => {
    try {
      setLoading(true)
      // Получаем детали фичи
      const featureResponse = await get<Feature>(`/orchestrator/features/${id}`)
      setFeature(featureResponse.data)
      
      // Получаем задачи фичи
      const tasksResponse = await get<Task[]>(`/orchestrator/features/${id}/tasks`)
      setTasks(tasksResponse.data)
      
      // Получаем запуски графов фичи
      const runsResponse = await get<GraphRun[]>(`/orchestrator/features/${id}/runs`)
      setRuns(runsResponse.data)
      // Дополнительно: артефакты и QA-отчёт (не критично)
      try {
        const artResp = await get<any>(`/orchestrator/features/${id}/artifacts`)
        setArtifacts(artResp.data)
      } catch {}
      try {
        const qaResp = await get<any>(`/orchestrator/features/${id}/qa-report`)
        setQaReport(qaResp.data)
      } catch {}
      
      setError(null)
    } catch (err) {
      console.error('Error fetching data:', err)
      setError('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchData()
    }
  }, [id])

  const handlePlanFeature = async () => {
    try {
      setPlanning(true)
      // Планируем фичу
      await post(`/orchestrator/features/${id}/plan`)
      // Обновляем данные
      await fetchData()
    } catch (err) {
      console.error('Error planning feature:', err)
      setError('Failed to plan feature')
    } finally {
      setPlanning(false)
    }
  }

  const handleRunFeature = async () => {
    try {
      setRunning(true)
      // Запускаем фичу
      await post(`/orchestrator/features/${id}/run`)
      // Обновляем данные
      await fetchData()
    } catch (err) {
      console.error('Error running feature:', err)
      setError('Failed to run feature')
    } finally {
      setRunning(false)
    }
  }

  const handleRetryTask = async (taskId: number) => {
    try {
      // В реальности: await post(`/orchestrator/tasks/${taskId}/retry`)
      console.log('Retrying task:', taskId)
      await fetchData()
    } catch (err) {
      console.error('Error retrying task:', err)
      setError('Failed to retry task')
    }
  }

  const handleRestartRun = async (runId: string) => {
    try {
      // В реальности: await post(`/orchestrator/runs/${runId}/restart`)
      console.log('Restarting run:', runId)
      await fetchData()
    } catch (err) {
      console.error('Error restarting run:', err)
      setError('Failed to restart run')
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'NEW':
        return 'default'
      case 'PLANNED':
        return 'secondary'
      case 'RUNNING':
        return 'default'
      case 'DONE':
        return 'secondary'
      case 'FAILED':
        return 'destructive'
      default:
        return 'default'
    }
  }

  const getTaskStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'NEW':
        return 'default'
      case 'RUNNING':
        return 'default'
      case 'DONE':
        return 'secondary'
      case 'FAILED':
        return 'destructive'
      case 'WAIT_BUDGET':
        return 'outline'
      case 'RETRYABLE':
        return 'secondary'
      default:
        return 'default'
    }
  }

  const getRunStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'default'
      case 'DONE':
        return 'secondary'
      case 'FAILED':
        return 'destructive'
      case 'PENDING':
        return 'outline'
      default:
        return 'default'
    }
  }

  // общий форматтер дат

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
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

  if (!feature) {
    return (
      <div className="text-center py-12">
        <Library className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Фича не найдена</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Фича с указанным ID не существует.
        </p>
        <div className="mt-6">
          <Button asChild>
            <Link to="features">Вернуться к списку фич</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-blue-50/30 dark:from-gray-900 dark:to-blue-900/20 min-h-screen">

      {/* Красивый заголовок */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center space-x-3 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md px-6 py-3 rounded-full shadow-lg">
          <Target className="h-6 w-6 text-blue-600 animate-pulse" />
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            {feature.title}
          </h1>
          <GitBranch className="h-6 w-6 text-purple-600" />
        </div>
        <div className="flex items-center justify-center space-x-4">
          <Badge variant="outline" className="text-sm">#{feature.id}</Badge>
          <Badge variant={getStatusBadgeVariant(feature.status)} className="text-sm">
            {feature.status}
          </Badge>
          <span className="text-gray-600 dark:text-gray-300">
            {feature.created_by} • {formatDate(feature.created_at)}
          </span>
        </div>
      </div>

      {/* Панель управления графом */}
      <GraphControlPanel
        feature={feature}
        runs={runs}
        tasks={tasks}
        onRefresh={fetchData}
      />

      {/* Таймлайн выполнения */}
      <FeatureTimeline
        feature={feature}
        tasks={tasks}
        runs={runs}
        onRetryTask={handleRetryTask}
        onRestartRun={handleRestartRun}
      />

      {/* Flight Map */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg font-medium flex items-center space-x-2">
            <Layers className="h-5 w-5" />
            <span>Карта выполнения</span>
          </CardTitle>
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RotateCcw className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>
          <FeatureFlightMap tasks={tasks} runs={runs} />
        </CardContent>
      </Card>

      {/* Информационные карточки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        {/* Приоритет */}
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">{feature.priority}</div>
                <div className="text-xs text-purple-600 dark:text-purple-400">Приоритет</div>
              </div>
              <div className="bg-purple-200 dark:bg-purple-800 p-2 rounded-full">
                <Target className="h-5 w-5 text-purple-600 dark:text-purple-300" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Задачи */}
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">{tasks.length}</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">Всего задач</div>
              </div>
              <div className="bg-blue-200 dark:bg-blue-800 p-2 rounded-full">
                <Layers className="h-5 w-5 text-blue-600 dark:text-blue-300" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Запуски */}
        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-700 dark:text-green-300">{runs.length}</div>
                <div className="text-xs text-green-600 dark:text-green-400">Запусков</div>
              </div>
              <div className="bg-green-200 dark:bg-green-800 p-2 rounded-full">
                <GitBranch className="h-5 w-5 text-green-600 dark:text-green-300" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Окружение */}
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-lg font-bold text-yellow-700 dark:text-yellow-300">{feature.env}</div>
                <div className="text-xs text-yellow-600 dark:text-yellow-400">Окружение</div>
              </div>
              <div className="bg-yellow-200 dark:bg-yellow-800 p-2 rounded-full">
                <Settings className="h-5 w-5 text-yellow-600 dark:text-yellow-300" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Intent JSON - если есть */}
      {feature.intent_json && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium flex items-center space-x-2">
              <Library className="h-5 w-5" />
              <span>Intent Configuration</span>
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigator.clipboard.writeText(JSON.stringify(feature.intent_json, null, 2))}
            >
              Копировать
            </Button>
          </CardHeader>
          <CardContent>
            <pre className="text-sm bg-gray-900 dark:bg-gray-950 text-green-400 p-4 rounded-lg overflow-x-auto max-h-64">
              {JSON.stringify(feature.intent_json, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Watchdog и дополнительная информация */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Watchdog */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4" />
              <span>Watchdog</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {watchdog ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Решение:</span>
                  <Badge variant={watchdog.decision === 'ESCALATE_L1' ? 'destructive' : 'secondary'}>
                    {watchdog.decision}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Ошибки:</span>
                  <span className="text-sm font-bold">{watchdog.failuresCount}</span>
                </div>
                {watchdog.context && (
                  <div className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded max-h-24 overflow-auto">
                    {watchdog.context.slice(0, 100)}...
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-500 text-center py-4">
                <AlertTriangle className="mx-auto h-8 w-8 mb-2 text-gray-300" />
                Нет данных
              </div>
            )}
          </CardContent>
        </Card>

        {/* Артефакты */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Library className="h-4 w-4" />
              <span>Артефакты</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {artifacts ? (
              <div className="space-y-2">
                <div className="text-xs">
                  <span className="font-medium">Run ID:</span> {artifacts.run_id?.slice(-8)}
                </div>
                <div className="text-xs">
                  <span className="font-medium">Директория:</span> {artifacts.artifacts_dir?.split('/').pop()}
                </div>
                {artifacts.manifest?.files?.length && (
                  <div className="text-xs">
                    <span className="font-medium">Файлов:</span> {artifacts.manifest.files.length}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-500 text-center py-4">
                <Library className="mx-auto h-8 w-8 mb-2 text-gray-300" />
                Нет артефактов
              </div>
            )}
          </CardContent>
        </Card>

        {/* QA Report */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <TestTube className="h-4 w-4" />
              <span>QA Отчёт</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {qaReport ? (
              <div className="space-y-2">
                <Badge variant="secondary" className="text-xs">
                  Есть отчёт
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => window.open(`/qa-reports/${feature.id}`, '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-1" />
                  Открыть
                </Button>
              </div>
            ) : (
              <div className="text-sm text-gray-500 text-center py-4">
                <TestTube className="mx-auto h-8 w-8 mb-2 text-gray-300" />
                Нет отчёта
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Задачи и запуски - компактно */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Задачи */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium flex items-center space-x-2">
              <Layers className="h-5 w-5" />
              <span>Задачи ({tasks.length})</span>
            </CardTitle>
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {tasks.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {tasks.map((task) => (
                  <Link
                    key={task.id}
                    to={`/tasks/${task.id}`}
                    className="block p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Badge variant={getTaskStatusBadgeVariant(task.status)} className="text-xs">
                          {task.status}
                        </Badge>
                        <span className="text-sm font-medium">{task.role}</span>
                        {task.attempts > 1 && (
                          <Badge variant="outline" className="text-xs">
                            #{task.attempts}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">#{task.id}</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Layers className="mx-auto h-8 w-8 mb-2 text-gray-300" />
                <p className="text-sm">Нет задач</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Запуски */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium flex items-center space-x-2">
              <GitBranch className="h-5 w-5" />
              <span>Запуски ({runs.length})</span>
            </CardTitle>
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {runs.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {runs.map((run) => (
                  <Link
                    key={run.run_id}
                    to={`/runs/${run.run_id}`}
                    className="block p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        <Badge variant={getRunStatusBadgeVariant(run.status)} className="text-xs">
                          {run.status}
                        </Badge>
                        <span className="text-sm font-medium">
                          {run.graph_name || 'Unknown'}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 font-mono">
                        {run.run_id.slice(-8)}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(run.last_checkpoint_at)}
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <GitBranch className="mx-auto h-8 w-8 mb-2 text-gray-300" />
                <p className="text-sm">Нет запусков</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Логи фичи - компактный превью */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg font-medium flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Логи фичи</span>
          </CardTitle>
          <Button variant="outline" size="sm" asChild>
            <Link to={`/logs?feature_id=${feature.id}`}>
              <ExternalLink className="h-4 w-4 mr-1" />
              Все логи
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          <FeatureLogsPreview featureId={feature.id} />
        </CardContent>
      </Card>
    </div>
  )
}

export default FeatureDetail

// Вспомогательный превью-компонент логов фичи
const FeatureLogsPreview: React.FC<{ featureId: number }> = ({ featureId }) => {
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    (async () => {
      try {
        const resp = await get<any[]>(`/logs/tail?limit=20&feature_id=${featureId}`)
        setLogs(resp.data || [])
      } catch {
        setLogs([])
      } finally { setLoading(false) }
    })()
  }, [featureId])
  if (loading) return <div className="text-sm text-gray-500">Загрузка…</div>
  if (!logs.length) return <div className="text-sm text-gray-500">Нет логов</div>
  return (
    <ul className="text-xs space-y-1 max-h-48 overflow-auto">
      {logs.slice(0,10).map((l, idx) => (
        <li key={idx} className={['ERROR','CRITICAL'].includes((l.level||'').toUpperCase()) ? 'text-red-600' : ''}>
          [{formatDate(l.ts)}] {l.level} {l.component}: {l.event}
        </li>
      ))}
    </ul>
  )
}
