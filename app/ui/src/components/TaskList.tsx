import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { 
  Layers, 
  Search,
  RefreshCw,
  Filter,
  Play,
  CheckCircle,
  Clock,
  XCircle
} from 'lucide-react'
import { get } from '@/lib/api'
import { Link } from 'react-router-dom'
import { formatDate } from '@/lib/format'

interface Task {
  id: number
  role: string
  status: string
  // Optional fields when backend provides extended view
  feature_id?: number
  feature_title?: string
  attempts?: number
  scheduled_at?: string
  started_at?: string
}

interface TaskListProps {
  onRefresh?: () => void
}

const TaskList: React.FC<TaskListProps> = ({ onRefresh }) => {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [roleFilter, setRoleFilter] = useState<string>('all')

  const fetchData = async () => {
    try {
      setLoading(true)
      // Получаем список задач
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

  // Фильтрация задач
  const filteredTasks = tasks.filter(task => {
    // Поиск по тексту
    if (searchTerm &&
        !(task.feature_title || '').toLowerCase().includes(searchTerm.toLowerCase()) &&
        !task.id.toString().includes(searchTerm) &&
        !(task.feature_id?.toString() || '').includes(searchTerm)) {
      return false
    }
    
    // Фильтр по статусу
    if (statusFilter !== 'all' && task.status !== statusFilter) {
      return false
    }
    
    // Фильтр по роли
    if (roleFilter !== 'all' && task.role !== roleFilter) {
      return false
    }
    
    return true
  })

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

  // общий форматтер дат

  // Получение уникальных статусов и ролей для фильтров
  const uniqueStatuses = ['all', ...Array.from(new Set(tasks.map(t => t.status)))]
  const uniqueRoles = ['all', ...Array.from(new Set(tasks.map(t => t.role)))]

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
      {/* Search and Filters */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Поиск по названию фичи или ID..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <select
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {uniqueStatuses.map(status => (
                <option key={status} value={status}>
                  {status === 'all' ? 'Все статусы' : status}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <select
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              {uniqueRoles.map(role => (
                <option key={role} value={role}>
                  {role === 'all' ? 'Все роли' : role}
                </option>
              ))}
            </select>
          </div>
        </div>
        
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

      {/* Task List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Список задач</CardTitle>
          <Layers className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {filteredTasks.length > 0 ? (
            <div className="space-y-3">
              {filteredTasks.map((task) => (
                <Link key={task.id} to={`/tasks/${task.id}`} className="block p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center">
                        <h3 className="text-sm font-medium">Задача #{task.id}</h3>
                        <Badge 
                          variant={getStatusBadgeVariant(task.status)} 
                          className="ml-2"
                        >
                          {task.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Роль: {task.role}{task.feature_id ? ` • Фича #${task.feature_id}` : ''}
                      </p>
                      {task.scheduled_at && (
                        <p className="text-xs text-muted-foreground">
                          Запланировано: {formatDate(task.scheduled_at)}{typeof task.attempts === 'number' ? ` • Попытки: ${task.attempts}` : ''}
                        </p>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет задач, соответствующих фильтрам
            </p>
          )}
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="text-sm text-muted-foreground">
        Всего задач: {filteredTasks.length}
      </div>
    </div>
  )
}

export default TaskList
