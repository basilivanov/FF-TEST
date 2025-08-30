import React, { useState, useEffect } from 'react'
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
  AlertTriangle
} from 'lucide-react'
import { get, post } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { Link, useParams } from 'react-router-dom'

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
    <div className="space-y-6">
      {/* Feature Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{feature.title}</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Детали фичи #{feature.id}
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-2">
          <Button 
            onClick={handlePlanFeature}
            disabled={planning || feature.status !== 'NEW'}
          >
            {planning ? (
              <>
                <RotateCcw className="mr-2 h-4 w-4 animate-spin" />
                Планирование...
              </>
            ) : (
              <>
                <Layers className="mr-2 h-4 w-4" />
                План
              </>
            )}
          </Button>
          <Button 
            onClick={handleRunFeature}
            disabled={running || (feature.status !== 'PLANNED' && feature.status !== 'RUNNING')}
          >
            {running ? (
              <>
                <RotateCcw className="mr-2 h-4 w-4 animate-spin" />
                Запуск...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Запустить
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Feature Details */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Информация о фиче</CardTitle>
          <Library className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">ID</div>
              <div className="text-sm">{feature.id}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Статус</div>
              <div>
                <Badge variant={getStatusBadgeVariant(feature.status)}>
                  {feature.status}
                </Badge>
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Создано</div>
              <div className="text-sm">{formatDate(feature.created_at)}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Автор</div>
              <div className="text-sm">{feature.created_by}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Окружение</div>
              <div className="text-sm">{feature.env}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Приоритет</div>
              <div className="text-sm">{feature.priority}</div>
            </div>
          </div>
          
          {feature.intent_json && (
            <div className="mt-4">
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Intent JSON</div>
              <pre className="mt-1 text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                {JSON.stringify(feature.intent_json, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Artifacts */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Артефакты</CardTitle>
        </CardHeader>
        <CardContent>
          {artifacts ? (
            <div className="space-y-2 text-sm">
              <div>run_id: {artifacts.run_id}</div>
              <div>dir: {artifacts.artifacts_dir}</div>
              {artifacts.manifest?.files?.length ? (
                <>
                  <div className="font-semibold mt-2">Файлы из манифеста:</div>
                  <ul className="list-disc pl-5">
                    {artifacts.manifest.files.map((f: string) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ul>
                </>
              ) : (
                <div className="text-gray-500">Список файлов отсутствует</div>
              )}
            </div>
          ) : (
            <div className="text-gray-500">Артефакты не найдены</div>
          )}
        </CardContent>
      </Card>

      {/* QA Report */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">QA Отчёт</CardTitle>
        </CardHeader>
        <CardContent>
          {qaReport ? (
            <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-64">{JSON.stringify(qaReport.qa_report || qaReport, null, 2)}</pre>
          ) : (
            <div className="text-gray-500">QA-отчёт отсутствует</div>
          )}
        </CardContent>
      </Card>

      {/* Tasks */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Задачи фичи</CardTitle>
          <Layers className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {tasks.length > 0 ? (
            <div className="space-y-3">
              {tasks.map((task) => (
                <Link key={task.id} to={`/tasks/${task.id}`} className="block p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center">
                        <h3 className="text-sm font-medium">Задача #{task.id}</h3>
                        <Badge 
                          variant={getTaskStatusBadgeVariant(task.status)} 
                          className="ml-2"
                        >
                          {task.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Роль: {task.role} • Попытки: {task.attempts}
                      </p>
                    </div>
                    <div className="text-right text-xs text-muted-foreground">
                      Запланировано: {formatDate(task.scheduled_at)}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет задач для этой фичи
            </p>
          )}
        </CardContent>
  </Card>

      {/* Runs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Запуски графов</CardTitle>
          <Play className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {runs.length > 0 ? (
            <div className="space-y-3">
              {runs.map((run) => (
                <Link key={run.run_id} to={`/runs/${run.run_id}`} className="block p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center">
                        <h3 className="text-sm font-medium">Запуск #{run.run_id}</h3>
                        <Badge 
                          variant={getRunStatusBadgeVariant(run.status)} 
                          className="ml-2"
                        >
                          {run.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Граф: {run.graph_name} • Поток: {run.thread_id}
                      </p>
                    </div>
                    <div className="text-right text-xs text-muted-foreground">
                      Последний чекпоинт: {formatDate(run.last_checkpoint_at)}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет запусков для этой фичи
            </p>
          )}
        </CardContent>
      </Card>

      {/* Feature-scoped logs (preview) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Логи фичи</CardTitle>
          <Link to={`/logs?feature_id=${feature.id}`} className="text-xs text-blue-600 flex items-center"><Link2 className="h-3 w-3 mr-1"/>Открыть все</Link>
        </CardHeader>
        <CardContent>
          <FeatureLogsPreview featureId={feature.id} />
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-end">
        <Button 
          variant="outline" 
          onClick={fetchData}
          disabled={loading}
        >
          <RotateCcw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Обновить
        </Button>
      </div>
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
