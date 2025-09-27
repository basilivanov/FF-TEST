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
  AlertTriangle,
  TrendingUp,
  Zap,
  Target,
  Timer,
  Cpu,
  MemoryStick,
  GitBranch,
  Users,
  Code,
  TestTube,
  BookOpen,
  Wrench
} from 'lucide-react'
import { get } from '@/lib/api'
import { formatDate, formatRelativeDate, formatGraphRunStatus, formatRole } from '@/lib/format'
import Mermaid from '@/components/Mermaid'
import { Sparkline } from '@/components/Sparkline'
import { ProgressRing } from '@/components/ProgressRing'

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
  execution_time_ms?: number
  context_tokens?: number
  output_tokens?: number
}

interface Milestone {
  id: string
  title: string
  description: string
  status: 'completed' | 'in_progress' | 'pending' | 'failed'
  timestamp?: string
  duration_ms?: number
  role?: string
  icon: React.ComponentType<any>
}

interface RunMetrics {
  total_execution_time: number
  peak_memory_usage: number
  avg_cpu_usage: number
  total_tokens: number
  error_count: number
  success_rate: number
}

const RunDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<GraphStatus | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [logsAll, setLogsAll] = useState<any[]>([])
  const [metrics, setMetrics] = useState<RunMetrics | null>(null)
  const [tab, setTab] = useState<'pipeline' | 'milestones' | 'metrics' | 'logs'>('pipeline')

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

      // Mock metrics data
      const mockMetrics: RunMetrics = {
        total_execution_time: Math.floor(Math.random() * 120000) + 30000, // 30-150 seconds
        peak_memory_usage: Math.floor(Math.random() * 500) + 100, // 100-600 MB
        avg_cpu_usage: Math.floor(Math.random() * 70) + 15, // 15-85%
        total_tokens: Math.floor(Math.random() * 15000) + 5000, // 5k-20k tokens
        error_count: Math.floor(Math.random() * 3), // 0-2 errors
        success_rate: Math.floor(Math.random() * 30) + 70 // 70-100%
      }
      setMetrics(mockMetrics)

      setError(null)
    } catch (e) {
      console.error('RunDetail: fetch error', e)
      setError('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  // Generate pipeline milestones based on tasks and run status
  const milestones = useMemo((): Milestone[] => {
    const getRoleIcon = (role: string) => {
      switch (role) {
        case 'Architect': return Users
        case 'Dev': return Code
        case 'QA': return TestTube
        case 'Scribe': return BookOpen
        case 'Maintainer': return Wrench
        default: return Activity
      }
    }

    const getTaskStatus = (task: Task): Milestone['status'] => {
      switch (task.status) {
        case 'DONE': return 'completed'
        case 'RUNNING': return 'in_progress'
        case 'FAILED': return 'failed'
        default: return 'pending'
      }
    }

    const baseMilestones: Milestone[] = [
      {
        id: 'init',
        title: 'Инициализация',
        description: 'Запуск пайплайна и подготовка контекста',
        status: 'completed',
        timestamp: data?.last_checkpoint,
        icon: Zap
      }
    ]

    // Add task-based milestones
    const taskMilestones = tasks.map((task): Milestone => ({
      id: `task-${task.id}`,
      title: formatRole(task.role),
      description: `Выполнение задачи ${formatRole(task.role).toLowerCase()}`,
      status: getTaskStatus(task),
      timestamp: task.started_at,
      duration_ms: task.execution_time_ms,
      role: task.role,
      icon: getRoleIcon(task.role)
    }))

    // Add completion milestone
    const completionStatus = data?.status === 'DONE' ? 'completed' :
                           data?.status === 'FAILED' ? 'failed' : 'pending'

    const finalMilestone: Milestone = {
      id: 'completion',
      title: 'Завершение',
      description: data?.status === 'DONE' ? 'Пайплайн успешно завершен' :
                  data?.status === 'FAILED' ? 'Пайплайн завершен с ошибкой' :
                  'Ожидание завершения',
      status: completionStatus,
      timestamp: data?.status === 'DONE' ? data.last_checkpoint : undefined,
      icon: Target
    }

    return [...baseMilestones, ...taskMilestones, finalMilestone]
  }, [tasks, data])

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

  // Generate performance data for sparklines
  const performanceData = useMemo(() => {
    return Array.from({ length: 20 }, () => Math.floor(Math.random() * 100) + 50)
  }, [metrics])

  const memoryData = useMemo(() => {
    return Array.from({ length: 20 }, () => Math.floor(Math.random() * 200) + 100)
  }, [metrics])

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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <ProgressRing
                value={getProgressPercentage(data.status)}
                max={100}
                size={40}
                strokeWidth={4}
                gradientFrom="#3B82F6"
                gradientTo="#1E40AF"
              />
              <div>
                <div className="text-2xl font-bold text-blue-600">{getProgressPercentage(data.status)}%</div>
                <div className="text-sm text-gray-600">завершено</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Timer className="h-8 w-8 text-green-600" />
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {metrics ? (metrics.total_execution_time / 1000).toFixed(0) : 0}s
                </div>
                <div className="text-sm text-gray-600">время выполнения</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <FileText className="h-8 w-8 text-purple-600" />
              <div>
                <div className="text-2xl font-bold text-purple-600">{tasks.length}</div>
                <div className="text-sm text-gray-600">задач в пайплайне</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              {data.status === 'DONE' ? (
                <CheckCircle className="h-8 w-8 text-green-600" />
              ) : data.status === 'FAILED' ? (
                <XCircle className="h-8 w-8 text-red-600" />
              ) : (
                <Clock className="h-8 w-8 text-blue-600" />
              )}
              <div>
                <div className="text-lg font-bold">{formatGraphRunStatus(data.status)}</div>
                <div className="text-sm text-gray-600">статус запуска</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-2 border-b pb-2 overflow-x-auto">
        <Button
          size="sm"
          variant={tab === 'pipeline' ? 'default' : 'outline'}
          onClick={() => setTab('pipeline')}
        >
          <GitBranch className="h-4 w-4 mr-2" />
          Пайплайн
        </Button>
        <Button
          size="sm"
          variant={tab === 'milestones' ? 'default' : 'outline'}
          onClick={() => setTab('milestones')}
        >
          <Target className="h-4 w-4 mr-2" />
          Вехи
        </Button>
        <Button
          size="sm"
          variant={tab === 'metrics' ? 'default' : 'outline'}
          onClick={() => setTab('metrics')}
        >
          <TrendingUp className="h-4 w-4 mr-2" />
          Метрики
        </Button>
        <Button
          size="sm"
          variant={tab === 'logs' ? 'default' : 'outline'}
          onClick={() => setTab('logs')}
        >
          <FileText className="h-4 w-4 mr-2" />
          Логи
        </Button>
      </div>

      {/* Pipeline Visualization */}
      {tab === 'pipeline' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <GitBranch className="h-5 w-5 mr-2" />
              Визуализация пайплайна
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Timeline */}
              <div className="relative">
                {milestones.map((milestone, index) => {
                  const Icon = milestone.icon
                  const isLast = index === milestones.length - 1

                  return (
                    <div key={milestone.id} className="relative flex items-start pb-6">
                      {/* Connector line */}
                      {!isLast && (
                        <div className="absolute left-6 top-12 w-0.5 h-full bg-gray-200 dark:bg-gray-700" />
                      )}

                      {/* Icon */}
                      <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-2 ${
                        milestone.status === 'completed' ? 'bg-green-100 border-green-500' :
                        milestone.status === 'in_progress' ? 'bg-blue-100 border-blue-500 animate-pulse' :
                        milestone.status === 'failed' ? 'bg-red-100 border-red-500' :
                        'bg-gray-100 border-gray-300'
                      }`}>
                        <Icon className={`h-6 w-6 ${
                          milestone.status === 'completed' ? 'text-green-600' :
                          milestone.status === 'in_progress' ? 'text-blue-600' :
                          milestone.status === 'failed' ? 'text-red-600' :
                          'text-gray-400'
                        }`} />
                      </div>

                      {/* Content */}
                      <div className="ml-4 flex-1">
                        <div className="flex items-center justify-between">
                          <h3 className="text-lg font-semibold">{milestone.title}</h3>
                          <div className="flex items-center space-x-2">
                            {milestone.duration_ms && (
                              <Badge variant="outline">
                                {(milestone.duration_ms / 1000).toFixed(1)}s
                              </Badge>
                            )}
                            <Badge variant={
                              milestone.status === 'completed' ? 'default' :
                              milestone.status === 'in_progress' ? 'secondary' :
                              milestone.status === 'failed' ? 'destructive' :
                              'outline'
                            }>
                              {milestone.status === 'completed' ? 'Завершено' :
                               milestone.status === 'in_progress' ? 'В процессе' :
                               milestone.status === 'failed' ? 'Ошибка' :
                               'Ожидание'}
                            </Badge>
                          </div>
                        </div>

                        <p className="text-gray-600 dark:text-gray-300 mt-1">
                          {milestone.description}
                        </p>

                        {milestone.timestamp && (
                          <p className="text-sm text-gray-500 mt-2">
                            {formatRelativeDate(milestone.timestamp)}
                          </p>
                        )}

                        {milestone.role && (
                          <Button size="sm" variant="link" asChild className="p-0 h-auto mt-2">
                            <Link to={`/tasks/${tasks.find(t => t.role === milestone.role)?.id}`}>
                              Перейти к задаче →
                            </Link>
                          </Button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Overall progress */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Общий прогресс</span>
                  <span className="text-sm text-gray-600">{getProgressPercentage(data.status)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      data.status === 'DONE' ? 'bg-green-500' :
                      data.status === 'FAILED' ? 'bg-red-500' :
                      data.status === 'RUNNING' ? 'bg-blue-500' : 'bg-gray-400'
                    }`}
                    style={{ width: `${getProgressPercentage(data.status)}%` }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Milestones Details */}
      {tab === 'milestones' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Target className="h-5 w-5 mr-2" />
                Ключевые события
              </CardTitle>
            </CardHeader>
            <CardContent>
              {logsMilestones.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Target className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Нет ключевых событий</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {logsMilestones.map((log, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                      <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="font-medium">{log.event}</div>
                        <div className="text-sm text-gray-600">{log.component}</div>
                        <div className="text-xs text-gray-500">{formatDate(log.ts)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <AlertTriangle className="h-5 w-5 mr-2" />
                Ошибки и предупреждения
              </CardTitle>
            </CardHeader>
            <CardContent>
              {logsErrors.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-500" />
                  <p>Ошибок не обнаружено</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {logsErrors.map((log, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                      <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="font-medium text-red-800">{log.event}</div>
                        <div className="text-sm text-red-600">{log.component}</div>
                        <div className="text-xs text-red-500">{formatDate(log.ts)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Performance Metrics */}
      {tab === 'metrics' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <Timer className="h-4 w-4" />
                  <span>Время выполнения</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {metrics ? (metrics.total_execution_time / 1000).toFixed(1) : 0}s
                </div>
                <div className="text-sm text-gray-600">общее время</div>
                <Sparkline
                  data={performanceData}
                  width={100}
                  height={30}
                  color="#3B82F6"
                  animate={true}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <MemoryStick className="h-4 w-4" />
                  <span>Пиковая память</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {metrics?.peak_memory_usage || 0} MB
                </div>
                <div className="text-sm text-gray-600">максимум</div>
                <Sparkline
                  data={memoryData}
                  width={100}
                  height={30}
                  color="#10B981"
                  animate={true}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <Cpu className="h-4 w-4" />
                  <span>CPU</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">
                  {metrics?.avg_cpu_usage || 0}%
                </div>
                <div className="text-sm text-gray-600">средняя загрузка</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-orange-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${metrics?.avg_cpu_usage || 0}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4" />
                  <span>Успешность</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-emerald-600">
                  {metrics?.success_rate || 0}%
                </div>
                <div className="text-sm text-gray-600">коэффициент успеха</div>
                <ProgressRing
                  value={metrics?.success_rate || 0}
                  max={100}
                  size={40}
                  strokeWidth={3}
                  gradientFrom="#10B981"
                  gradientTo="#059669"
                />
              </CardContent>
            </Card>
          </div>

          {/* Token Usage */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="h-5 w-5 mr-2" />
                Использование токенов
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{metrics?.total_tokens || 0}</div>
                  <div className="text-sm text-gray-600">всего токенов</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {tasks.reduce((sum, task) => sum + (task.context_tokens || 0), 0)}
                  </div>
                  <div className="text-sm text-gray-600">контекст</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {tasks.reduce((sum, task) => sum + (task.output_tokens || 0), 0)}
                  </div>
                  <div className="text-sm text-gray-600">вывод</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detailed Logs */}
      {tab === 'logs' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Подробные логи запуска
            </CardTitle>
          </CardHeader>
          <CardContent>
            {logsAll.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Логи не найдены</p>
              </div>
            ) : (
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
                {logsAll.map((log, index) => (
                  <div key={index} className="mb-1">
                    <span className="text-gray-500">[{formatDate(log.ts)}]</span>{' '}
                    <span className={`font-medium ${
                      log.level === 'ERROR' ? 'text-red-400' :
                      log.level === 'WARN' ? 'text-yellow-400' :
                      log.level === 'INFO' ? 'text-blue-400' :
                      'text-gray-400'
                    }`}>
                      {log.level}
                    </span>{' '}
                    <span className="text-gray-300">{log.component}:</span>{' '}
                    <span>{log.event}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
