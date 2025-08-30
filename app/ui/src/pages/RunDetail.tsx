import React, { useEffect, useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { 
  ArrowLeft,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Activity,
  FileText,
  AlertTriangle
} from 'lucide-react'
import { get } from '@/lib/api'
import { formatDate, formatRelativeDate, formatGraphRunStatus, formatRole } from '@/lib/format'
import Mermaid from '@/components/Mermaid'

interface GraphStatus {
  run_id: string
  graph: string
  status: string
  feature_status: string
  last_checkpoint: string
  env: string
  feature_id?: number
  feature_title?: string
}

interface Task {
  id: number
  feature_id: number
  role: string
  status: string
  attempts: number
  started_at?: string
  finished_at?: string
  scheduled_at: string
}

const RunDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<GraphStatus | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [logsAll, setLogsAll] = useState<any[]>([])
  const [tab, setTab] = useState<'milestones'|'errors'|'all'>('milestones')

  const fetchRunDetails = async () => {
    if (!id) return

    try {
      setLoading(true)
      
      // Получаем информацию о run'е
      const resp = await get<GraphStatus>(`/orchestrator/graph/${id}/status`)
      setData(resp.data)

      // Получаем задачи для этой фичи (если есть feature_id)
      if (resp.data?.feature_id) {
        try {
          const tasksResponse = await get<Task[]>(`/orchestrator/tasks?feature_id=${resp.data.feature_id}`)
          setTasks(tasksResponse.data)
        } catch (tasksError) {
          console.warn('Failed to fetch tasks:', tasksError)
          setTasks([])
        }
      }
      // Логи запуска
      try {
        const logs = await get<any[]>(`/logs/tail?limit=200&run_id=${id}`)
        setLogsAll(logs.data || [])
      } catch {
        setLogsAll([])
      }
      
      setError(null)
    } catch (e) {
      console.error('RunDetail: fetch error', e)
      setError('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRunDetails()
  }, [id])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return <Clock className="h-4 w-4 text-blue-500" />
      case 'DONE':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'FAILED':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getTaskStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return <Play className="h-4 w-4 text-blue-500 animate-spin" />
      case 'DONE':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'FAILED':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'NEW':
        return <Clock className="h-4 w-4 text-gray-500" />
      case 'WAIT_BUDGET':
        return <Clock className="h-4 w-4 text-yellow-500" />
      default:
        return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getProgressPercentage = (status: string): number => {
    switch (status) {
      case 'DONE':
        return 100
      case 'FAILED':
        return 0
      case 'RUNNING':
        return 65
      default:
        return 10
    }
  }

  const roles = useMemo(() => {
    // определяем последовательность ролей из задач, либо дефолт
    const order = tasks.map(t => t.role)
    const uniq: string[] = []
    order.forEach(r => { if (r && !uniq.includes(r)) uniq.push(r) })
    return uniq.length ? uniq : ['Architect','Dev','QA','Scribe','Maintainer']
  }, [tasks])

  const currentTask = useMemo(() => tasks.find(t => t.status === 'RUNNING') || tasks.find(t => ['NEW','WAIT_BUDGET'].includes(t.status)) || tasks[0], [tasks])
  const currentRole = currentTask?.role

  const mermaidChart = useMemo(() => {
    const nodes = roles.map(r => r).join(' --> ')
    const labels = roles.map(r => `${r}[${formatRole(r)}]`).join('\n')
    const classDef = 'classDef current fill:#93c5fd,stroke:#1d4ed8,stroke-width:2px,color:#111;'
    const classApply = currentRole ? `class ${currentRole} current;` : ''
    return `graph LR\n${labels}\n${nodes}\n${classDef}\n${classApply}`
  }, [roles, currentRole])

  const milestoneEvents = useMemo(() => new Set(['job_started','job_finished','task_started','task_finished']), [])
  const logsMilestones = logsAll.filter(l => milestoneEvents.has((l.event||'').toString()))
  const logsErrors = logsAll.filter(l => ['ERROR','CRITICAL'].includes((l.level||'').toUpperCase()))

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link to="runs">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Назад к запускам
            </Link>
          </Button>
        </div>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          <strong className="font-bold">Ошибка! </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Run не найден</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Запуск с указанным ID не существует.</p>
        <div className="mt-6">
          <Button asChild>
            <Link to="runs">Вернуться к списку</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link to="runs">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Назад к запускам
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {data.feature_title || `Фича #${data.feature_id || 'Unknown'}`}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Запуск {data.run_id}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon(data.status)}
          <Badge variant={data.status === 'DONE' ? 'secondary' : data.status === 'FAILED' ? 'destructive' : 'default'}>
            {formatGraphRunStatus(data.status)}
          </Badge>
          {data.feature_id && (
            <Button size="sm" variant="outline" asChild>
              <Link to={`/features/${data.feature_id}`}>К фиче</Link>
            </Button>
          )}
        </div>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            Прогресс выполнения
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-sm">Текущий шаг: {currentRole ? formatRole(currentRole) : '—'} {currentTask ? (<Button asChild size="sm" variant="link"><Link to={`/tasks/${currentTask.id}`}>к задаче →</Link></Button>) : null}</div>
            <Mermaid chart={mermaidChart} />
            <div className="flex items-center">
              <div className="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${
                    data.status === 'DONE' ? 'bg-green-500' : 
                    data.status === 'FAILED' ? 'bg-red-500' : 
                    data.status === 'RUNNING' ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'
                  }`} 
                  style={{ width: `${getProgressPercentage(data.status)}%` }}
                ></div>
              </div>
              <div className="ml-4 text-sm font-medium min-w-16">
                {getProgressPercentage(data.status)}%
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Граф:</span> {data.graph}
              </div>
              <div>
                <span className="text-gray-500">Статус фичи:</span> {data.feature_status}
              </div>
              <div>
                <span className="text-gray-500">Среда:</span> {data.env}
              </div>
              <div>
                <span className="text-gray-500">Последняя точка:</span> {formatRelativeDate(data.last_checkpoint)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tasks */}
      {tasks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Задачи ({tasks.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {tasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getTaskStatusIcon(task.status)}
                    <div>
                      <p className="text-sm font-medium">{formatRole(task.role)}</p>
                      <p className="text-xs text-muted-foreground">
                        Задача #{task.id} • Попытки: {task.attempts}
                      </p>
                      {task.started_at && (
                        <p className="text-xs text-muted-foreground">
                          Начала: {formatRelativeDate(task.started_at)}
                        </p>
                      )}
                    </div>
                  </div>
                  <div>
                    <Badge 
                      variant={
                        task.status === 'DONE' ? 'secondary' : 
                        task.status === 'FAILED' ? 'destructive' :
                        task.status === 'RUNNING' ? 'default' : 'outline'
                      }
                    >
                      {task.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Logs (Run-scoped) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center"><FileText className="h-5 w-5 mr-2"/>Логи запуска</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-3 flex gap-2 text-sm">
            <Button size="sm" variant={tab==='milestones'?'default':'outline'} onClick={()=>setTab('milestones')}>Основные вехи</Button>
            <Button size="sm" variant={tab==='errors'?'default':'outline'} onClick={()=>setTab('errors')}>Ошибки</Button>
            <Button size="sm" variant={tab==='all'?'default':'outline'} onClick={()=>setTab('all')}>Все логи</Button>
          </div>
          {tab==='milestones' && (
            logsMilestones.length === 0 ? <div className="text-sm text-gray-500">Нет записей</div> : (
              <ul className="text-sm space-y-1">
                {logsMilestones.map((l, i) => (
                  <li key={i}>[{formatDate(l.ts)}] {l.level} {l.component}: {l.event}</li>
                ))}
              </ul>
            )
          )}
          {tab==='errors' && (
            logsErrors.length === 0 ? <div className="text-sm text-gray-500">Нет ошибок</div> : (
              <ul className="text-sm space-y-1">
                {logsErrors.map((l, i) => (
                  <li key={i} className="text-red-600 flex items-center"><AlertTriangle className="h-4 w-4 mr-1"/>[{formatDate(l.ts)}] {l.component}: {l.event}</li>
                ))}
              </ul>
            )
          )}
          {tab==='all' && (
            logsAll.length === 0 ? <div className="text-sm text-gray-500">Нет логов</div> : (
              <ul className="text-sm space-y-1">
                {logsAll.map((l, i) => (
                  <li key={i}>[{formatDate(l.ts)}] {l.level} {l.component}: {l.event}</li>
                ))}
              </ul>
            )
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2">
        <Button onClick={fetchRunDetails} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Обновить
        </Button>
      </div>
    </div>
  )
}

export default RunDetail
