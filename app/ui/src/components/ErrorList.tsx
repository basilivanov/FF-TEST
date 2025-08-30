import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { 
  AlertTriangle, 
  Search,
  RefreshCw,
  Filter
} from 'lucide-react'
import { get } from '@/lib/api'
import { formatDate } from '@/lib/format'

interface LogEntry {
  ts: string
  level: string
  component: string
  agent_role: string
  event: string
  correlation_id: string
  kv: Record<string, any>
}

interface ErrorListProps {
  onRefresh?: () => void
}

const ErrorList: React.FC<ErrorListProps> = ({ onRefresh }) => {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    agentRole: '',
    component: '',
    correlationId: ''
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      // Пытаемся прямой эндпоинт ошибок
      const logsResponse = await get<LogEntry[]>('/logs/errors', { headers: { 'X-Suppress-Alert': '1' } })
      const onlyErrors = (logsResponse.data || []).filter(l => ['ERROR','CRITICAL'].includes((l.level||'').toUpperCase()))
      setLogs(onlyErrors)
      setError(null)
    } catch (err1) {
      console.warn('ErrorList: /logs/errors failed, trying fallback /logs/tail', err1)
      try {
        // Фолбэк: берём хвост логов и фильтруем ошибки
        const tail = await get<LogEntry[]>(`/logs/tail?limit=500`, { headers: { 'X-Suppress-Alert': '1' } })
        const onlyErrors = (tail.data || []).filter(l => ['ERROR','CRITICAL'].includes((l.level||'').toUpperCase()))
        setLogs(onlyErrors)
        setError(null)
      } catch (err2) {
        console.error('ErrorList: fallback /logs/tail failed', err2)
        setError('Failed to fetch data')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Обновляем данные каждые 30 секунд
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Фильтрация логов
  const filteredLogs = logs.filter(log => {
    // Поиск по тексту
    if (searchTerm && 
        !log.event.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !log.component.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !log.agent_role.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    
    // Фильтры
    if (filters.agentRole && log.agent_role !== filters.agentRole) {
      return false
    }
    
    if (filters.component && log.component !== filters.component) {
      return false
    }
    
    if (filters.correlationId && log.correlation_id !== filters.correlationId) {
      return false
    }
    
    return true
  })

  // Получение уникальных значений для фильтров
  const uniqueAgentRoles = Array.from(new Set(logs.map(log => log.agent_role)))
  const uniqueComponents = Array.from(new Set(logs.map(log => log.component)))

  // Используем общий форматтер дат (поддержка unix sec/ms)

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
        <div className="md:col-span-2 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Поиск по событиям, компонентам, ролям..."
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
              value={filters.agentRole}
              onChange={(e) => setFilters({...filters, agentRole: e.target.value})}
            >
              <option value="">Все роли</option>
              {uniqueAgentRoles.map(role => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </div>
        </div>
        
        <div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <select
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              value={filters.component}
              onChange={(e) => setFilters({...filters, component: e.target.value})}
            >
              <option value="">Все компоненты</option>
              {uniqueComponents.map(component => (
                <option key={component} value={component}>{component}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Error List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Ошибки и предупреждения</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {filteredLogs.length > 0 ? (
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {filteredLogs.map((log, index) => (
                <div 
                  key={index} 
                  className={`p-4 rounded-lg border ${
                    log.level === 'ERROR' 
                      ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-700' 
                      : 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">
                      {formatDate(log.ts)}
                    </span>
                    <Badge 
                      variant={
                        log.level === 'ERROR' ? 'destructive' : 'secondary'
                      }
                    >
                      {log.level}
                    </Badge>
                  </div>
                  <p className={`text-sm font-medium mt-1 ${
                    log.level === 'ERROR' 
                      ? 'text-red-800 dark:text-red-200' 
                      : 'text-yellow-800 dark:text-yellow-200'
                  }`}>
                    {log.event}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {log.component} • {log.agent_role} • ID: {log.correlation_id}
                  </p>
                  {log.kv && Object.keys(log.kv).length > 0 && (
                    <div className="mt-2 text-xs">
                      {Object.entries(log.kv).map(([key, value]) => (
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
              Нет ошибок или предупреждений
            </p>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <div className="text-sm text-muted-foreground">
          Всего записей: {filteredLogs.length}
        </div>
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

export default ErrorList
