import React, { useState, useEffect, useRef } from 'react'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { Badge } from '@/shadcn/ui/badge'
import { 
  Search, 
  Pause, 
  Play, 
  Copy,
  Filter,
  Calendar,
  AlertCircle,
  Info,
  AlertTriangle,
  XCircle,
  CheckCircle,
  FileText,
  ChevronLeft,
  ChevronRight,
  Eye,
  ExternalLink,
  X
} from 'lucide-react'
import { formatDate } from '@/lib/format'
import { get } from '@/lib/api'
import { useLocation } from 'react-router-dom'

// Реальная схема API
interface LogEntry {
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL'
  service: string
  message: string
  correlation_id: string | null
  request_id: string | null
  user: string | null
  source: string
  feature_id: number | null
  task_id: number | null
  run_id: string | null
  duration_ms: number | null
  status_code: number | null
  ip_address: string | null
  user_agent: string | null
  error: string | null
  context: Record<string, any> | null
}

interface LogsResponse {
  items: LogEntry[]
  total: number
}

interface LogDetailResponse {
  id: string
  timestamp: string
  level: string
  service: string
  message: string
  task_id?: string | null
  feature_id?: string | null
  request_id?: string | null
  details: Record<string, any>
}

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [total, setTotal] = useState(0)
  const [liveTail, setLiveTail] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('ALL')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageLimit] = useState(50)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const tailInterval = useRef<NodeJS.Timeout | null>(null)
  const [lastTailTimestamp, setLastTailTimestamp] = useState<string>('')
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null)
  const [logDetail, setLogDetail] = useState<LogDetailResponse | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Level options for filtering
  const levelOptions = ['ALL', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']

  const fetchLogs = async (page: number = 1, level: string = 'ALL', q: string = '') => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams({
        page: page.toString(),
        limit: pageLimit.toString()
      })
      
      if (level !== 'ALL') {
        params.set('level', level)
      }
      
      if (q.trim()) {
        params.set('q', q.trim())
      }
      
      const response = await get<LogsResponse>(`/logs?${params.toString()}`)
      const data = response.data
      
      setLogs(data.items)
      setTotal(data.total)
      
      // Обновляем timestamp для tail если есть данные
      if (data.items.length > 0) {
        setLastTailTimestamp(data.items[0].timestamp)
      }
      
    } catch (err) {
      console.error('Logs fetch error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch logs')
      setLogs([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const fetchTail = async () => {
    if (!lastTailTimestamp) return
    
    try {
      const params = new URLSearchParams({
        after_ts: lastTailTimestamp,
        limit: '100'
      })
      
      if (levelFilter !== 'ALL') {
        params.set('level', levelFilter)
      }
      
      if (searchTerm.trim()) {
        params.set('q', searchTerm.trim())
      }
      
      const response = await get<LogsResponse>(`/logs/tail?${params.toString()}`)
      const data = response.data
      
      if (data.items.length > 0) {
        setLogs(prev => [...data.items, ...prev])
        setLastTailTimestamp(data.items[0].timestamp)
        setTotal(prev => prev + data.items.length)
      }
      
    } catch (err) {
      console.warn('Tail fetch failed:', err)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchLogs(currentPage, levelFilter, searchTerm)
  }, [currentPage, levelFilter, searchTerm])

  // Live tail setup
  useEffect(() => {
    if (liveTail && lastTailTimestamp) {
      tailInterval.current = setInterval(fetchTail, 3000) // 3 seconds
    } else {
      if (tailInterval.current) {
        clearInterval(tailInterval.current)
        tailInterval.current = null
      }
    }
    
    return () => {
      if (tailInterval.current) {
        clearInterval(tailInterval.current)
      }
    }
  }, [liveTail, lastTailTimestamp, levelFilter, searchTerm])

  // Auto-scroll when live tail is active
  useEffect(() => {
    if (liveTail && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, liveTail])

  const toggleLiveTail = () => {
    setLiveTail(!liveTail)
  }

  const handleRefresh = () => {
    fetchLogs(currentPage, levelFilter, searchTerm)
  }

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage)
  }

  const copyLogToClipboard = (log: LogEntry) => {
    const logText = `[${log.timestamp}] ${log.level} ${log.service}: ${log.message} ${log.correlation_id ? `corr:${log.correlation_id}` : ''}`
    navigator.clipboard.writeText(logText)
  }

  const fetchLogDetail = async (logId: string) => {
    try {
      setDetailLoading(true)
      const response = await get<LogDetailResponse>(`/logs/${logId}`)
      setLogDetail(response.data)
    } catch (err) {
      console.error('Failed to fetch log detail:', err)
      setLogDetail(null)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleRowClick = (log: LogEntry) => {
    if (log.correlation_id) {
      setSelectedLogId(log.correlation_id)
      fetchLogDetail(log.correlation_id)
    }
  }

  const closeDrawer = () => {
    setSelectedLogId(null)
    setLogDetail(null)
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const filterByService = (service: string) => {
    setSearchTerm(service)
    setCurrentPage(1)
    closeDrawer()
  }

  const filterByLevel = (level: string) => {
    setLevelFilter(level)
    setCurrentPage(1)
    closeDrawer()
  }

  const getLogLevelIcon = (level: string) => {
    switch (level) {
      case 'DEBUG':
        return <Info className="h-4 w-4 text-blue-500" />
      case 'INFO':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'WARN':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'ERROR':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'FATAL':
        return <XCircle className="h-4 w-4 text-red-800" />
      default:
        return <Info className="h-4 w-4 text-gray-500" />
    }
  }

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'DEBUG': return 'text-blue-400'
      case 'INFO': return 'text-green-400'
      case 'WARN': return 'text-yellow-400'
      case 'ERROR': return 'text-red-400'
      case 'FATAL': return 'text-red-600'
      default: return 'text-gray-400'
    }
  }

  const totalPages = Math.ceil(total / pageLimit)

  return (
    <div className="space-y-6">
      {/* Error banner */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center justify-between" role="alert">
          <div className="flex items-center">
            <XCircle className="h-4 w-4 mr-2"/>
            Ошибка загрузки: {error}
          </div>
          <Button size="sm" variant="outline" onClick={handleRefresh} disabled={loading}>
            {loading ? 'Повтор…' : 'Повторить'}
          </Button>
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Logs</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Системные логи с фильтрацией и Live tail
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-2">
          <Button onClick={toggleLiveTail} variant={liveTail ? 'default' : 'outline'}>
            {liveTail ? (
              <>
                <Pause className="mr-2 h-4 w-4" />
                Стоп Live
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Live tail
              </>
            )}
          </Button>
          <Button onClick={handleRefresh} variant="outline" disabled={loading}>
            {loading ? 'Загрузка…' : 'Обновить'}
          </Button>
        </div>
      </div>

      {/* Controls */}
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-4 md:space-y-0">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Поиск по сообщению или correlation_id..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Уровень:</span>
              {levelOptions.map(level => (
                <Badge
                  key={level}
                  variant={levelFilter === level ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => {
                    setLevelFilter(level)
                    setCurrentPage(1) // Reset to first page
                  }}
                >
                  {level === 'ALL' ? 'Все' : level}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Всего записей: {total} | Страница {currentPage} из {totalPages}
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1 || loading}
          >
            <ChevronLeft className="h-4 w-4" />
            Пред
          </Button>
          <span className="px-3 py-1 text-sm">
            {currentPage} / {totalPages}
          </span>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages || loading}
          >
            След
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Loading skeleton */}
      {loading && logs.length === 0 && (
        <div className="border rounded-lg bg-gray-50 dark:bg-gray-900 p-6">
          <div className="animate-pulse space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex space-x-4">
                <div className="h-4 w-20 bg-gray-300 dark:bg-gray-700 rounded"></div>
                <div className="h-4 w-16 bg-gray-300 dark:bg-gray-700 rounded"></div>
                <div className="h-4 flex-1 bg-gray-300 dark:bg-gray-700 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs Table */}
      {!loading && logs.length > 0 && (
        <div className="border rounded-lg overflow-hidden bg-gray-900 text-gray-100">
          <div className="overflow-y-auto max-h-[calc(100vh-400px)]">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-800 sticky top-0">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Время
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Уровень
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Сервис
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Сообщение
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    ID
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {logs.map((log, index) => (
                  <tr 
                    key={`${log.correlation_id}-${index}`} 
                    className="hover:bg-gray-800 cursor-pointer transition-colors"
                    onClick={() => handleRowClick(log)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-1 text-gray-400" />
                        {formatDate(log.timestamp)}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        {getLogLevelIcon(log.level)}
                        <span className={`ml-1 text-sm font-medium ${getLogLevelColor(log.level)}`}>
                          {log.level}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <Badge variant="outline" className="text-xs">
                        {log.service}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm max-w-md">
                      <div className="truncate" title={log.message}>
                        {log.message}
                      </div>
                      {log.error && (
                        <div className="text-xs text-red-400 mt-1 truncate" title={log.error}>
                          Error: {log.error}
                        </div>
                      )}
                      {log.context && Object.keys(log.context).length > 0 && (
                        <div className="text-xs text-gray-400 mt-1">
                          {JSON.stringify(log.context).slice(0, 100)}...
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="space-y-1">
                        {log.correlation_id && (
                          <div className="text-xs text-blue-400 font-mono">
                            {log.correlation_id}
                          </div>
                        )}
                        {log.task_id && (
                          <div className="text-xs text-purple-400">
                            task:{log.task_id}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            copyLogToClipboard(log)
                          }}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRowClick(log)
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div ref={logsEndRef} />
        </div>
      )}

      {/* Empty state */}
      {!loading && logs.length === 0 && (
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Логи не найдены</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {error ? 'Проверьте подключение к API' : 'Попробуйте изменить фильтры или период поиска'}
          </p>
          <Button variant="outline" onClick={handleRefresh} className="mt-4">
            Обновить
          </Button>
        </div>
      )}

      {/* Bottom pagination */}
      {!loading && logs.length > 0 && totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handlePageChange(Math.max(1, currentPage - 5))}
            disabled={currentPage <= 1}
          >
            ««
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <span className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-800 rounded">
            {currentPage} / {totalPages}
          </span>
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handlePageChange(Math.min(totalPages, currentPage + 5))}
            disabled={currentPage >= totalPages}
          >
            »»
          </Button>
        </div>
      )}

      {/* Log Detail Drawer */}
      {selectedLogId && (
        <div className="fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black bg-opacity-50" 
            onClick={closeDrawer}
          />
          
          {/* Drawer Panel */}
          <div className="relative ml-auto w-full max-w-2xl bg-white dark:bg-gray-900 h-full overflow-y-auto shadow-xl">
            {/* Header */}
            <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Детали лога
              </h2>
              <Button variant="ghost" size="sm" onClick={closeDrawer}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Content */}
            <div className="p-6 space-y-6">
              {detailLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  <span className="ml-2 text-sm text-gray-500">Загрузка деталей...</span>
                </div>
              ) : logDetail ? (
                <>
                  {/* Basic Info */}
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      {getLogLevelIcon(logDetail.level)}
                      <span className={`font-medium ${getLogLevelColor(logDetail.level)}`}>
                        {logDetail.level}
                      </span>
                      <Badge variant="outline">{logDetail.service}</Badge>
                      <span className="text-xs text-gray-500">
                        {formatDate(logDetail.timestamp)}
                      </span>
                    </div>
                    
                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Сообщение</h3>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {logDetail.message}
                      </p>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(logDetail.id)}
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      Копировать ID
                    </Button>
                    
                    {logDetail.task_id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(`/admin/tasks/${logDetail.task_id}`, '_blank')}
                      >
                        <ExternalLink className="mr-2 h-4 w-4" />
                        Открыть Таск
                      </Button>
                    )}
                    
                    {logDetail.feature_id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(`/admin/features/${logDetail.feature_id}`, '_blank')}
                      >
                        <ExternalLink className="mr-2 h-4 w-4" />
                        Открыть Фичу
                      </Button>
                    )}
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => filterByService(logDetail.service)}
                    >
                      <Filter className="mr-2 h-4 w-4" />
                      Фильтр по сервису
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => filterByLevel(logDetail.level)}
                    >
                      <Filter className="mr-2 h-4 w-4" />
                      Фильтр по уровню
                    </Button>
                  </div>
                  
                  {/* IDs Section */}
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">Идентификаторы</h3>
                    <div className="grid grid-cols-1 gap-3">
                      <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                        <div className="text-xs text-gray-500 mb-1">Correlation ID</div>
                        <div className="text-sm font-mono text-blue-600 dark:text-blue-400">
                          {logDetail.id}
                        </div>
                      </div>
                      
                      {logDetail.request_id && (
                        <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                          <div className="text-xs text-gray-500 mb-1">Request ID</div>
                          <div className="text-sm font-mono text-purple-600 dark:text-purple-400">
                            {logDetail.request_id}
                          </div>
                        </div>
                      )}
                      
                      {logDetail.task_id && (
                        <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                          <div className="text-xs text-gray-500 mb-1">Task ID</div>
                          <div className="text-sm font-mono text-green-600 dark:text-green-400">
                            {logDetail.task_id}
                          </div>
                        </div>
                      )}
                      
                      {logDetail.feature_id && (
                        <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                          <div className="text-xs text-gray-500 mb-1">Feature ID</div>
                          <div className="text-sm font-mono text-orange-600 dark:text-orange-400">
                            {logDetail.feature_id}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Details JSON */}
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">Детали (JSON)</h3>
                    <div className="bg-gray-900 dark:bg-gray-950 p-4 rounded-lg overflow-auto">
                      <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                        {JSON.stringify(logDetail.details, null, 2)}
                      </pre>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="mx-auto h-8 w-8 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-500">Не удалось загрузить детали лога</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Logs