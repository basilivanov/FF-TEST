import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { 
  Play, 
  Clock, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  RefreshCw
} from 'lucide-react'
import { get } from '@/lib/api'
import { formatDate } from '@/lib/format'

interface RunningTask {
  id: number
  feature_id: number
  feature_title: string
  role: string
  status: string
  started_at: string
  elapsed_ms: number
}

interface LastEvent {
  ts: string
  level: string
  component: string
  agent_role: string
  event: string
  kv: Record<string, any>
}

interface RunningTasksProps {
  onRefresh?: () => void
}

const RunningTasks: React.FC<RunningTasksProps> = ({ onRefresh }) => {
  const [runningTasks, setRunningTasks] = useState<RunningTask[]>([])
  const [lastEvents, setLastEvents] = useState<LastEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      // Получаем запущенные задачи
      const tasksResponse = await get<RunningTask[]>('/orchestrator/tasks')
      // Фильтруем только запущенные задачи
      const running = tasksResponse.data.filter(task => task.status === 'RUNNING')
      setRunningTasks(running)
      
      // Получаем последние события
      const eventsResponse = await get<LastEvent[]>('/logs/tail?limit=10')
      setLastEvents(eventsResponse.data)
      
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
    // Обновляем данные каждые 5 секунд
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const formatElapsedTime = (elapsedMs: number) => {
    const seconds = Math.floor(elapsedMs / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`
    } else {
      return `${seconds}s`
    }
  }

  // формат даты берём из общего форматтера (поддерживает unix sec/ms и ISO)

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
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Running Tasks */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Текущие задачи</CardTitle>
          <Play className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {runningTasks.length > 0 ? (
            <div className="space-y-3">
              {runningTasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">{task.feature_title}</p>
                    <p className="text-xs text-muted-foreground">Задача #{task.id} • {task.role}</p>
                    <p className="text-xs text-muted-foreground">Начало: {formatDate(task.started_at)}</p>
                  </div>
                  <div className="text-right">
                    <Badge variant="default">
                      <Clock className="h-3 w-3 mr-1" />
                      {formatElapsedTime(task.elapsed_ms)}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет запущенных задач
            </p>
          )}
        </CardContent>
      </Card>

      {/* Last Events */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Последние события</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {lastEvents.length > 0 ? (
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {lastEvents.map((event, index) => (
                <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">
                      {formatDate(event.ts)}
                    </span>
                    <Badge 
                      variant={
                        event.level === 'ERROR' ? 'destructive' : 
                        event.level === 'WARNING' ? 'secondary' : 
                        'default'
                      }
                    >
                      {event.level}
                    </Badge>
                  </div>
                  <p className="text-sm font-medium mt-1">{event.event}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {event.component} • {event.agent_role}
                  </p>
                  {event.kv && Object.keys(event.kv).length > 0 && (
                    <div className="mt-2 text-xs">
                      {Object.entries(event.kv).map(([key, value]) => (
                        <div key={key} className="truncate">
                          <span className="font-medium">{key}:</span> {String(value)}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет событий
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default RunningTasks
