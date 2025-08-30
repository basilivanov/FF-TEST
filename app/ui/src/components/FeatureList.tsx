import React, { useState, useEffect, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { 
  Library, 
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

interface Feature {
  id: number
  title: string
  intent_json: any
  status: string
  priority: number
  created_at: string
  created_by: string
  env: string
}

interface FeatureListProps {
  onRefresh?: () => void
}

const FeatureList: React.FC<FeatureListProps> = ({ onRefresh }) => {
  const [features, setFeatures] = useState<Feature[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  // Поддержка множественного фильтра статусов через query-параметр (?status=NEW,PLANNED)
  const [statusFilterFromUrl, setStatusFilterFromUrl] = useState<string[] | null>(null)
  const location = useLocation()

  const fetchData = async () => {
    try {
      setLoading(true)
      // Получаем список фич
      const featuresResponse = await get<Feature[]>('/orchestrator/features')
      setFeatures(featuresResponse.data)
      
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

  // Разбор статусов из URL: ?status=NEW,PLANNED или ?status=NEW&status=PLANNED
  useEffect(() => {
    try {
      const params = new URLSearchParams(location.search)
      const statusParams = params.getAll('status')
      if (statusParams.length === 0) {
        setStatusFilterFromUrl(null)
        return
      }
      // Если статус один и содержит запятую — разбиваем
      const expanded = statusParams
        .flatMap((s) => s.split(','))
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean)
      setStatusFilterFromUrl(expanded.length > 0 ? Array.from(new Set(expanded)) : null)
    } catch (e) {
      console.warn('Failed to parse status from URL', e)
      setStatusFilterFromUrl(null)
    }
  }, [location.search])

  // Фильтрация фич
  const filteredFeatures = features.filter(feature => {
    // Поиск по тексту
    if (searchTerm && 
        !feature.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !feature.id.toString().includes(searchTerm)) {
      return false
    }
    
    // Фильтр по статусу (URL имеет приоритет, поддерживает множественный выбор)
    if (statusFilterFromUrl && statusFilterFromUrl.length > 0) {
      if (!statusFilterFromUrl.includes(feature.status)) return false
    } else {
      if (statusFilter !== 'all' && feature.status !== statusFilter) return false
    }
    
    return true
  })

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'NEW':
        return 'default'
      case 'PLANNED':
        return 'secondary'
      case 'RUNNING':
        return 'default'
      case 'DONE':
        return 'secondary'
      case 'FAILED':
        return 'destructive'
      default:
        return 'default'
    }
  }

  // Получение уникальных статусов для фильтра
  const uniqueStatuses = ['all', ...Array.from(new Set(features.map(f => f.status)))]

  const urlFilterLabel = useMemo(() => {
    if (!statusFilterFromUrl || statusFilterFromUrl.length === 0) return null
    return statusFilterFromUrl.join(', ')
  }, [statusFilterFromUrl])

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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Поиск по названию или ID..."
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
          {urlFilterLabel && (
            <div className="mt-1 text-xs text-blue-600 dark:text-blue-300">
              Фильтр из URL: {urlFilterLabel}
            </div>
          )}
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

      {/* Feature List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Список фич</CardTitle>
          <Library className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {filteredFeatures.length > 0 ? (
            <div className="space-y-3">
              {filteredFeatures.map((feature) => (
                <Link key={feature.id} to={`/features/${feature.id}`} className="block p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center">
                        <h3 className="text-sm font-medium">{feature.title}</h3>
                        <Badge 
                          variant={getStatusBadgeVariant(feature.status)} 
                          className="ml-2"
                        >
                          {feature.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        ID: {feature.id} • {feature.env} • Создано: {formatDate(feature.created_at)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Создал: {feature.created_by} • Приоритет: {feature.priority}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2"></div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
              Нет фич, соответствующих фильтрам
            </p>
          )}
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="text-sm text-muted-foreground">
        Всего фич: {filteredFeatures.length}
      </div>
    </div>
  )
}

export default FeatureList
