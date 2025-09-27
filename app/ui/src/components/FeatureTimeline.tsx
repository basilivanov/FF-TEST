import React, { useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import {
  CheckCircle,
  Clock,
  Play,
  XCircle,
  AlertTriangle,
  User,
  Calendar,
  ArrowRight,
  Zap,
  GitBranch,
  FileText,
  Settings,
  TestTube,
  Rocket,
  Eye,
  Brain,
  Code,
  Search,
  Target,
  Activity
} from 'lucide-react'
import { formatDate } from '@/lib/format'
import { Sparkline } from '@/components/Sparkline'

interface Task {
  id: number
  feature_id: number
  role: string
  status: string
  attempts: number
  scheduled_at: string
  started_at?: string
  completed_at?: string
  updated_at?: string
  error_message?: string
  correlation_id?: string
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

interface Feature {
  id: number
  title: string
  status: string
  created_at: string
  updated_at?: string
  created_by: string
  priority: number
  env: string
}

interface FeatureTimelineProps {
  feature: Feature
  tasks: Task[]
  runs: GraphRun[]
  onRetryTask?: (taskId: number) => void
  onRestartRun?: (runId: string) => void
}

interface TimelineEvent {
  id: string
  type: 'feature_created' | 'task_scheduled' | 'task_started' | 'task_completed' | 'task_failed' | 'run_started' | 'run_completed' | 'run_failed'
  timestamp: string
  title: string
  description: string
  status: 'success' | 'warning' | 'error' | 'info' | 'pending'
  details?: any
  canRetry?: boolean
  actionable?: boolean
}

const ROLE_ICONS = {
  'Architect': Brain,
  'Dev': Code,
  'QA': TestTube,
  'Scribe': FileText,
  'Apply': Rocket,
  'Gate': Eye,
  'Watchdog': AlertTriangle
}

const ROLE_COLORS = {
  'Architect': 'bg-purple-100 text-purple-700 border-purple-200',
  'Dev': 'bg-blue-100 text-blue-700 border-blue-200',
  'QA': 'bg-green-100 text-green-700 border-green-200',
  'Scribe': 'bg-yellow-100 text-yellow-700 border-yellow-200',
  'Apply': 'bg-red-100 text-red-700 border-red-200',
  'Gate': 'bg-indigo-100 text-indigo-700 border-indigo-200',
  'Watchdog': 'bg-orange-100 text-orange-700 border-orange-200'
}

const FeatureTimeline: React.FC<FeatureTimelineProps> = ({
  feature,
  tasks,
  runs,
  onRetryTask,
  onRestartRun
}) => {

  // Объединяем все события в единый таймлайн
  const events: TimelineEvent[] = useMemo(() => {
    const allEvents: TimelineEvent[] = []

    // Создание фичи
    allEvents.push({
      id: `feature-${feature.id}`,
      type: 'feature_created',
      timestamp: feature.created_at,
      title: 'Фича создана',
      description: `Создана пользователем ${feature.created_by}`,
      status: 'info',
      details: {
        priority: feature.priority,
        env: feature.env
      }
    })

    // События задач
    tasks.forEach(task => {
      // Планирование задачи
      allEvents.push({
        id: `task-scheduled-${task.id}`,
        type: 'task_scheduled',
        timestamp: task.scheduled_at,
        title: `Задача ${task.role} запланирована`,
        description: `Роль: ${task.role}, попыток: ${task.attempts}`,
        status: 'info',
        details: task
      })

      // Начало выполнения
      if (task.started_at) {
        allEvents.push({
          id: `task-started-${task.id}`,
          type: 'task_started',
          timestamp: task.started_at,
          title: `Задача ${task.role} начата`,
          description: 'Выполняется...',
          status: task.status === 'RUNNING' ? 'warning' : 'info',
          details: task
        })
      }

      // Завершение задачи
      if (task.completed_at) {
        allEvents.push({
          id: `task-completed-${task.id}`,
          type: task.status === 'DONE' ? 'task_completed' : 'task_failed',
          timestamp: task.completed_at,
          title: `Задача ${task.role} ${task.status === 'DONE' ? 'завершена' : 'провалилась'}`,
          description: task.error_message || (task.status === 'DONE' ? 'Успешно выполнена' : 'Ошибка выполнения'),
          status: task.status === 'DONE' ? 'success' : 'error',
          details: task,
          canRetry: task.status === 'FAILED',
          actionable: true
        })
      }
    })

    // События запусков графов
    runs.forEach(run => {
      allEvents.push({
        id: `run-started-${run.run_id}`,
        type: 'run_started',
        timestamp: run.created_at || run.last_checkpoint_at,
        title: `Запуск графа начат`,
        description: `Граф: ${run.graph_name || 'неизвестно'}, поток: ${run.thread_id}`,
        status: 'info',
        details: run
      })

      if (run.status === 'DONE' || run.status === 'FAILED') {
        allEvents.push({
          id: `run-completed-${run.run_id}`,
          type: run.status === 'DONE' ? 'run_completed' : 'run_failed',
          timestamp: run.updated_at || run.last_checkpoint_at,
          title: `Запуск графа ${run.status === 'DONE' ? 'завершён' : 'провалился'}`,
          description: run.status === 'DONE' ? 'Успешно выполнен' : 'Ошибка в графе',
          status: run.status === 'DONE' ? 'success' : 'error',
          details: run,
          canRetry: run.status === 'FAILED',
          actionable: true
        })
      }
    })

    // Сортируем по времени (новые сверху)
    return allEvents.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }, [feature, tasks, runs])

  const getEventIcon = (event: TimelineEvent) => {
    switch (event.type) {
      case 'feature_created':
        return <Target className="h-4 w-4" />
      case 'task_scheduled':
        return <Calendar className="h-4 w-4" />
      case 'task_started':
        return <Play className="h-4 w-4" />
      case 'task_completed':
        return <CheckCircle className="h-4 w-4" />
      case 'task_failed':
        return <XCircle className="h-4 w-4" />
      case 'run_started':
        return <GitBranch className="h-4 w-4" />
      case 'run_completed':
        return <CheckCircle className="h-4 w-4" />
      case 'run_failed':
        return <XCircle className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const getEventColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-700 border-green-200'
      case 'error':
        return 'bg-red-100 text-red-700 border-red-200'
      case 'warning':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'info':
        return 'bg-blue-100 text-blue-700 border-blue-200'
      case 'pending':
        return 'bg-gray-100 text-gray-700 border-gray-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getDotColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-500'
      case 'error':
        return 'bg-red-500'
      case 'warning':
        return 'bg-yellow-500'
      case 'info':
        return 'bg-blue-500'
      case 'pending':
        return 'bg-gray-400'
      default:
        return 'bg-gray-400'
    }
  }

  const getRoleIcon = (role: string) => {
    const IconComponent = ROLE_ICONS[role as keyof typeof ROLE_ICONS] || User
    return <IconComponent className="h-4 w-4" />
  }

  const getProgress = () => {
    const totalTasks = tasks.length
    const completedTasks = tasks.filter(t => t.status === 'DONE').length
    const failedTasks = tasks.filter(t => t.status === 'FAILED').length
    const runningTasks = tasks.filter(t => t.status === 'RUNNING').length

    return {
      completed: totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0,
      failed: totalTasks > 0 ? (failedTasks / totalTasks) * 100 : 0,
      running: totalTasks > 0 ? (runningTasks / totalTasks) * 100 : 0,
      total: totalTasks,
      completedCount: completedTasks,
      failedCount: failedTasks,
      runningCount: runningTasks
    }
  }

  const progress = getProgress()

  // Генерируем данные для sparkline активности
  const activityData = useMemo(() => {
    const data = []
    for (let i = 0; i < 12; i++) {
      // Эмулируем активность на основе количества событий
      const value = Math.floor(Math.random() * events.length / 2) + 1
      data.push(value)
    }
    return data
  }, [events])

  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Таймлайн выполнения</span>
          </CardTitle>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-xs text-gray-500">Активность</div>
              <Sparkline
                data={activityData}
                width={60}
                height={16}
                color="#3B82F6"
                animate={true}
              />
            </div>
            <Badge variant={feature.status === 'COMPLETED' ? 'default' : 'secondary'}>
              {feature.status}
            </Badge>
          </div>
        </div>

        {/* Прогресс-бар */}
        <div className="mt-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span>Прогресс выполнения</span>
            <span>{progress.completedCount}/{progress.total} задач</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 flex overflow-hidden">
            <div
              className="bg-green-500 h-full transition-all duration-500"
              style={{ width: `${progress.completed}%` }}
            />
            <div
              className="bg-yellow-500 h-full transition-all duration-500"
              style={{ width: `${progress.running}%` }}
            />
            <div
              className="bg-red-500 h-full transition-all duration-500"
              style={{ width: `${progress.failed}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>{progress.completedCount} завершено</span>
            <span>{progress.runningCount} в работе</span>
            <span>{progress.failedCount} ошибок</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="max-h-96 overflow-y-auto">
          {events.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <Timeline className="mx-auto h-8 w-8 mb-2" />
              <p>Нет событий для отображения</p>
            </div>
          ) : (
            <div className="relative">
              {/* Вертикальная линия таймлайна */}
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200"></div>

              {events.map((event, index) => (
                <div key={event.id} className="relative flex items-start space-x-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  {/* Точка на таймлайне */}
                  <div className={`relative z-10 flex items-center justify-center w-3 h-3 rounded-full ${getDotColor(event.status)} ring-4 ring-white dark:ring-gray-900`}>
                  </div>

                  {/* Основной контент события */}
                  <div className="flex-1 min-w-0 pb-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-md text-xs font-medium border ${getEventColor(event.status)}`}>
                            {getEventIcon(event)}
                            <span>{event.title}</span>
                          </div>

                          {/* Роль для задач */}
                          {event.details?.role && (
                            <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-md text-xs border ${ROLE_COLORS[event.details.role as keyof typeof ROLE_COLORS] || 'bg-gray-100 text-gray-700 border-gray-200'}`}>
                              {getRoleIcon(event.details.role)}
                              <span>{event.details.role}</span>
                            </div>
                          )}

                          {/* Correlation ID */}
                          {event.details?.correlation_id && (
                            <Badge variant="outline" className="text-xs font-mono">
                              {event.details.correlation_id.slice(-8)}
                            </Badge>
                          )}
                        </div>

                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                          {event.description}
                        </p>

                        {/* Дополнительные детали */}
                        {event.details?.error_message && (
                          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-2 mb-2">
                            <p className="text-xs text-red-700 dark:text-red-300">{event.details.error_message}</p>
                          </div>
                        )}

                        {/* Время события */}
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <Calendar className="h-3 w-3" />
                          <span>{formatDate(event.timestamp)}</span>
                          {event.details?.attempts && event.details.attempts > 1 && (
                            <>
                              <span>•</span>
                              <span>Попытка #{event.details.attempts}</span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Действия */}
                      {event.actionable && (
                        <div className="ml-4 flex items-center space-x-2">
                          {event.canRetry && event.type.includes('task') && onRetryTask && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => onRetryTask(event.details.id)}
                              className="text-xs"
                            >
                              <ArrowRight className="h-3 w-3 mr-1" />
                              Повторить
                            </Button>
                          )}
                          {event.canRetry && event.type.includes('run') && onRestartRun && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => onRestartRun(event.details.run_id)}
                              className="text-xs"
                            >
                              <ArrowRight className="h-3 w-3 mr-1" />
                              Перезапуск
                            </Button>
                          )}
                          {event.details?.id && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                if (event.type.includes('task')) {
                                  window.open(`/tasks/${event.details.id}`, '_blank')
                                } else if (event.type.includes('run')) {
                                  window.open(`/runs/${event.details.run_id}`, '_blank')
                                }
                              }}
                              className="text-xs"
                            >
                              <Eye className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default FeatureTimeline