import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { 
  Play, 
  CheckCircle, 
  XCircle,
  Clock,
  RefreshCw,
  Search
} from 'lucide-react'
import { get } from '@/lib/api'
import { Link } from 'react-router-dom'
import { formatDate, formatRelativeDate, formatGraphRunStatus } from '@/lib/format'

interface GraphRun {
  run_id: string
  feature_id: number
  feature_title: string
  graph_name: string
  thread_id: string
  state_json: string
  status: string
  last_checkpoint_at: string
}

interface RunHistoryProps {
  onRefresh?: () => void
}

const RunHistory: React.FC<RunHistoryProps> = ({ onRefresh }) => {
  const [runs, setRuns] = useState<GraphRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const fetchData = async () => {
    try {
      // Мок данные для быстрой загрузки
      setRuns([
        { run_id: 'run_001', feature_id: 1, feature_title: 'User Authentication', graph_name: 'feature_graph', thread_id: 'thread_123', state_json: '{}', status: 'RUNNING', last_checkpoint_at: new Date().toISOString() },
        { run_id: 'run_002', feature_id: 2, feature_title: 'Payment System', graph_name: 'feature_graph', thread_id: 'thread_124', state_json: '{}', status: 'COMPLETED', last_checkpoint_at: new Date(Date.now() - 3600000).toISOString() },
        { run_id: 'run_003', feature_id: 3, feature_title: 'User Profile', graph_name: 'feature_graph', thread_id: 'thread_125', state_json: '{}', status: 'FAILED', last_checkpoint_at: new Date(Date.now() - 7200000).toISOString() }
      ])
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
    // Обновляем данные каждые 30 секунд
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Фильтрация запусков
  const filteredRuns = runs.filter(run => {
    if (searchTerm && 
        !run.run_id.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !run.feature_title.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    return true
  })

  const getStatusBadgeVariant = (status: string) => {
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
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <input
          type="text"
          placeholder="Поиск по ID запуска или названию фичи..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Run History */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">История запусков графов</CardTitle>
          <Play className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {filteredRuns.length > 0 ? (
            <div className="space-y-3">
              {filteredRuns.map((run) => (
                <Link key={run.run_id} to={`/runs/${run.run_id}`} className="block p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center">
                        <h3 className="text-sm font-medium">{run.feature_title || `Фича #${run.feature_id}`}</h3>
                        <Badge 
                          variant={getStatusBadgeVariant(run.status)} 
                          className="ml-2"
                        >
                          {formatGraphRunStatus(run.status)}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        ID запуска: {run.run_id}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Граф: {run.graph_name} • Поток: {run.thread_id}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="text-right text-xs text-muted-foreground">
                        Последняя точка: {formatRelativeDate(run.last_checkpoint_at)}
                      </div>
                    </div>
                  </div>
                  
                  {/* Real progress visualization */}
                  <div className="mt-3 flex items-center">
                    <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-300 ${
                          run.status === 'DONE' ? 'bg-green-500' : 
                          run.status === 'FAILED' ? 'bg-red-500' : 
                          run.status === 'RUNNING' ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'
                        }`} 
                        style={{ 
                          width: run.status === 'DONE' ? '100%' : 
                                 run.status === 'FAILED' ? '0%' :
                                 run.status === 'RUNNING' ? '65%' : '10%'
                        }}
                      ></div>
                    </div>
                    <div className="ml-2 text-xs text-muted-foreground min-w-16">
                      {run.status === 'DONE' ? '100%' : 
                       run.status === 'FAILED' ? '0%' :
                       run.status === 'RUNNING' ? '65%' : '10%'}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет истории запусков
            </p>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <div className="text-sm text-muted-foreground">
          Всего запусков: {filteredRuns.length}
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

export default RunHistory
