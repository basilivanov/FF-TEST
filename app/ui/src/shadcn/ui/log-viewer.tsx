import React, { useState, useRef, useEffect } from 'react'
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
  CheckCircle
} from 'lucide-react'
import { formatLogLevel, formatDate } from '@/lib/format'
import { LogEntry, LogSeverity, Role } from '@/lib/types'

interface LogViewerProps {
  logs: LogEntry[]
  isStreaming?: boolean
  onToggleStreaming?: () => void
  onClearLogs?: () => void
  className?: string
}

const LogViewer: React.FC<LogViewerProps> = ({ 
  logs, 
  isStreaming = true, 
  onToggleStreaming,
  onClearLogs,
  className 
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [componentFilter, setComponentFilter] = useState<string | null>(null)
  const [levelFilter, setLevelFilter] = useState<LogSeverity[]>([])
  const [roleFilter, setRoleFilter] = useState<Role | null>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const logsEndRef = useRef<HTMLDivElement>(null)
  
  // Component options for filtering
  const componentOptions = Array.from(new Set(logs.map(log => log.component)))
  
  // Level options for filtering
  const levelOptions: LogSeverity[] = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
  
  // Role options for filtering
  const roleOptions = Array.from(new Set(logs.map(log => log.agent_role))) as Role[]

  // Scroll to bottom when new logs are added and auto-scroll is enabled
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  // Filter logs based on search term, component filter, level filter, and role filter
  const filteredLogs = logs.filter(log => {
    const matchesSearch = searchTerm === '' || 
      log.event.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.kv && JSON.stringify(log.kv).toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesComponent = componentFilter === null || log.component === componentFilter
    
    const matchesLevel = levelFilter.length === 0 || levelFilter.includes(log.level)
    
    const matchesRole = roleFilter === null || log.agent_role === roleFilter
    
    return matchesSearch && matchesComponent && matchesLevel && matchesRole
  })

  // Toggle auto-scroll
  const toggleAutoScroll = () => {
    setAutoScroll(!autoScroll)
  }

  // Copy log entry to clipboard
  const copyLogToClipboard = (log: LogEntry) => {
    const logText = `[${formatDate(log.ts)}] ${log.level} ${log.component} ${log.agent_role}: ${log.event} ${JSON.stringify(log.kv)}`
    navigator.clipboard.writeText(logText)
  }

  // Get log level icon
  const getLogLevelIcon = (level: LogSeverity) => {
    switch (level) {
      case 'DEBUG':
        return <Info className="h-4 w-4 text-blue-500" />
      case 'INFO':
        return <Info className="h-4 w-4 text-green-500" />
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'ERROR':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'CRITICAL':
        return <XCircle className="h-4 w-4 text-red-800" />
      default:
        return <Info className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Controls */}
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-4 md:space-y-0">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Поиск по событию или содержимому лога..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Компонент:</span>
              <Badge
                variant={!componentFilter ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => setComponentFilter(null)}
              >
                Все
              </Badge>
              {componentOptions.map(component => (
                <Badge
                  key={component}
                  variant={componentFilter === component ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => setComponentFilter(component)}
                >
                  {component}
                </Badge>
              ))}
            </div>
          </div>
        </div>
        
        <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-4 md:space-y-0">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Уровень:</span>
              <Badge
                variant={levelFilter.length === 0 ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => setLevelFilter([])}
              >
                Все
              </Badge>
              {levelOptions.map(level => (
                <Badge
                  key={level}
                  variant={levelFilter.includes(level) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => {
                    setLevelFilter(prev => 
                      prev.includes(level) 
                        ? prev.filter(l => l !== level) 
                        : [...prev, level]
                    )
                  }}
                >
                  <div className="flex items-center">
                    {getLogLevelIcon(level)}
                    <span className="ml-1">{formatLogLevel(level)}</span>
                  </div>
                </Badge>
              ))}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Роль:</span>
              <Badge
                variant={!roleFilter ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => setRoleFilter(null)}
              >
                Все
              </Badge>
              {roleOptions.map(role => (
                <Badge
                  key={role}
                  variant={roleFilter === role ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => setRoleFilter(role)}
                >
                  {role}
                </Badge>
              ))}
            </div>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="auto-scroll"
              checked={autoScroll}
              onChange={toggleAutoScroll}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="auto-scroll" className="text-sm text-gray-700 dark:text-gray-300">
              Автопрокрутка
            </label>
          </div>
          <div className="flex space-x-2">
            {onToggleStreaming && (
              <Button onClick={onToggleStreaming} variant={isStreaming ? 'default' : 'outline'}>
                {isStreaming ? (
                  <>
                    <Pause className="mr-2 h-4 w-4" />
                    Пауза
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Продолжить
                  </>
                )}
              </Button>
            )}
            {onClearLogs && (
              <Button onClick={onClearLogs} variant="outline">
                Очистить
              </Button>
            )}
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Всего записей: {logs.length} | Отфильтровано: {filteredLogs.length}
            </div>
          </div>
        </div>
      </div>

      {/* Logs Viewer */}
      <div className="border rounded-lg overflow-hidden bg-gray-900 text-gray-100">
        <div className="overflow-y-auto max-h-[calc(100vh-300px)]">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-800 sticky top-0">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Время
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Уровень
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Компонент
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Роль
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Событие
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Содержимое
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {filteredLogs.map((log, index) => (
                <tr key={index} className="hover:bg-gray-800">
                  <td className="px-6 py-3 whitespace-nowrap text-sm">
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1 text-gray-400" />
                      {formatDate(log.ts)}
                    </div>
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      {getLogLevelIcon(log.level)}
                      <span className="ml-1 text-sm font-medium">
                        {formatLogLevel(log.level)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm">
                    {log.component}
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm">
                    {log.agent_role}
                  </td>
                  <td className="px-6 py-3 text-sm">
                    {log.event}
                  </td>
                  <td className="px-6 py-3 text-sm">
                    {log.kv && (
                      <div className="truncate max-w-md">
                        {JSON.stringify(log.kv)}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm font-medium">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyLogToClipboard(log)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div ref={logsEndRef} />
      </div>

      {/* Empty state */}
      {filteredLogs.length === 0 && (
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Логи не найдены</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Попробуйте изменить параметры поиска или фильтрации.
          </p>
        </div>
      )}
    </div>
  )
}

export { LogViewer }