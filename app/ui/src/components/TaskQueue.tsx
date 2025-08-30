import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { 
  Layers, 
  Play, 
  Clock, 
  RefreshCw,
  Pause,
  RotateCcw
} from 'lucide-react'
import { get, post } from '@/lib/api'
import { formatDate, formatRelativeDate, formatTaskStatus, formatRole } from '@/lib/format'

interface Task {
  id: number
  feature_id: number
  feature_title: string
  role: string
  status: string
  attempts: number
  scheduled_at: string
  started_at?: string
}

interface TaskQueueProps {
  onRefresh?: () => void
}

const TaskQueue: React.FC<TaskQueueProps> = ({ onRefresh }) => {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryingTaskId, setRetryingTaskId] = useState<number | null>(null)
  const [pausingTaskId, setPausingTaskId] = useState<number | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      // Получаем все задачи
      const tasksResponse = await get<Task[]>('/orchestrator/tasks')
      setTasks(tasksResponse.data)
      
      setError(null)
    } catch (err) {
      console.error('Error fetching data:', err)
      setError('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Обновляем данные каждые 15 секунд
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [])

  const handleRetryTask = async (taskId: number) => {
    try {
      setRetryingTaskId(taskId)
      // В реальной реализации здесь будет вызов API для повторной попытки задачи
      // await post(`/api/v1/orchestrator/tasks/${taskId}/retry`)
      
      // Пока что просто обновляем данные
      await fetchData()
    } catch (err) {
      console.error('Error retrying task:', err)
      setError('Failed to retry task')
    } finally {
      setRetryingTaskId(null)
    }
  }

  const handlePauseTask = async (taskId: number) => {
    try {
      setPausingTaskId(taskId)
      // В реальной реализации здесь будет вызов API для паузы задачи
      // await post(`/api/v1/orchestrator/tasks/${taskId}/pause`)
      
      // Пока что просто обновляем данные
      await fetchData()
    } catch (err) {
      console.error('Error pausing task:', err)
      setError('Failed to pause task')
    } finally {
      setPausingTaskId(null)
    }
  }

  const getStatusBadgeVariant = (status: string) => {
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


  // Фильтруем задачи по статусам для отображения в разных секциях
  const newTasks = tasks.filter(task => task.status === 'NEW')
  const waitBudgetTasks = tasks.filter(task => task.status === 'WAIT_BUDGET')
  const retryableTasks = tasks.filter(task => task.status === 'RETRYABLE')

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

  return (
    <div className="space-y-6">
      {/* NEW Tasks */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Новые задачи (NEW)</CardTitle>
          <Layers className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {newTasks.length > 0 ? (
            <div className="space-y-3">
              {newTasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">{task.feature_title || `Фича #${task.feature_id}`}</p>
                    <p className="text-xs text-muted-foreground">Задача #{task.id} • {formatRole(task.role)}</p>
                    <p className="text-xs text-muted-foreground">Запланировано: {formatDate(task.scheduled_at)}</p>
                    <p className="text-xs text-gray-400">Попытки: {task.attempts}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={getStatusBadgeVariant(task.status)}>
                      {formatTaskStatus(task.status)}
                    </Badge>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleRetryTask(task.id)}
                      disabled={retryingTaskId === task.id}
                    >
                      {retryingTaskId === task.id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет новых задач
            </p>
          )}
        </CardContent>
      </Card>

      {/* WAIT_BUDGET Tasks */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Ожидают бюджета (WAIT_BUDGET)</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {waitBudgetTasks.length > 0 ? (
            <div className="space-y-3">
              {waitBudgetTasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">{task.feature_title || `Фича #${task.feature_id}`}</p>
                    <p className="text-xs text-muted-foreground">Задача #{task.id} • {formatRole(task.role)}</p>
                    <p className="text-xs text-muted-foreground">Запланировано: {formatDate(task.scheduled_at)}</p>
                    <p className="text-xs text-gray-400">Попытки: {task.attempts}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={getStatusBadgeVariant(task.status)}>
                      {formatTaskStatus(task.status)}
                    </Badge>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleRetryTask(task.id)}
                      disabled={retryingTaskId === task.id}
                    >
                      {retryingTaskId === task.id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет задач, ожидающих бюджета
            </p>
          )}
        </CardContent>
      </Card>

      {/* RETRYABLE Tasks */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Повторяемые (RETRYABLE)</CardTitle>
          <RotateCcw className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {retryableTasks.length > 0 ? (
            <div className="space-y-3">
              {retryableTasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">{task.feature_title || `Фича #${task.feature_id}`}</p>
                    <p className="text-xs text-muted-foreground">Задача #{task.id} • {formatRole(task.role)}</p>
                    <p className="text-xs text-muted-foreground">Попытки: {task.attempts}</p>
                    <p className="text-xs text-muted-foreground">Запланировано: {formatRelativeDate(task.scheduled_at)}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={getStatusBadgeVariant(task.status)}>
                      {formatTaskStatus(task.status)}
                    </Badge>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleRetryTask(task.id)}
                      disabled={retryingTaskId === task.id}
                    >
                      {retryingTaskId === task.id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handlePauseTask(task.id)}
                      disabled={pausingTaskId === task.id}
                    >
                      {pausingTaskId === task.id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Pause className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет повторяемых задач
            </p>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-end">
        <Button 
          onClick={fetchData}
          disabled={loading}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Обновить
        </Button>
      </div>
    </div>
  )
}

export default TaskQueue