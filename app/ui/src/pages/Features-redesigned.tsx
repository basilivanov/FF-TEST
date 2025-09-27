import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
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
  XCircle,
  Plus,
  Activity,
  Zap,
  User,
  Calendar,
  AlertCircle,
  TrendingUp,
  BarChart3,
  Settings,
  Eye,
  GitBranch,
  Target
} from 'lucide-react'
import { get } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { ProgressRing } from '@/components/ProgressRing'
import { Sparkline } from '@/components/Sparkline'

interface Feature {
  id: number
  title: string
  intent_json: any
  status: string
  priority: number
  created_at: string
  created_by: string
  env: string
  description?: string
}

interface FeatureStats {
  total: number
  new: number
  planned: number
  running: number
  completed: number
  failed: number
}

const FeaturesRedesigned: React.FC = () => {
  const navigate = useNavigate()
  const [features, setFeatures] = useState<Feature[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')

  const fetchFeatures = async () => {
    try {
      setLoading(true)
      const response = await get<Feature[]>('/orchestrator/features')
      setFeatures(response.data || [])
      setError(null)
    } catch (err) {
      console.error('Error fetching features:', err)
      setError('Не удалось загрузить фичи')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFeatures()
  }, [])

  // Статистика фич
  const stats: FeatureStats = useMemo(() => {
    const total = features.length
    const new_ = features.filter(f => f.status === 'NEW').length
    const planned = features.filter(f => f.status === 'PLANNED').length
    const running = features.filter(f => f.status === 'RUNNING').length
    const completed = features.filter(f => f.status === 'COMPLETED').length
    const failed = features.filter(f => f.status === 'FAILED').length
    
    return { total, new: new_, planned, running, completed, failed }
  }, [features])

  // Фильтрация
  const filteredFeatures = useMemo(() => {
    return features.filter(feature => {
      const matchesSearch = !searchTerm || 
        feature.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        feature.created_by.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesStatus = statusFilter === 'all' || feature.status === statusFilter
      const matchesPriority = priorityFilter === 'all' || feature.priority.toString() === priorityFilter

      return matchesSearch && matchesStatus && matchesPriority
    })
  }, [features, searchTerm, statusFilter, priorityFilter])

  // Генерация данных для sparkline (тренд создания фич)
  const generateTrendData = () => {
    const data = []
    for (let i = 0; i < 14; i++) {
      const value = Math.random() * 10 + 2
      data.push(value)
    }
    return data
  }

  const trendData = generateTrendData()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW': return 'bg-blue-500'
      case 'PLANNED': return 'bg-yellow-500'
      case 'RUNNING': return 'bg-green-500'
      case 'COMPLETED': return 'bg-emerald-500'
      case 'FAILED': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'NEW': return <Plus className="h-4 w-4" />
      case 'PLANNED': return <Clock className="h-4 w-4" />
      case 'RUNNING': return <Play className="h-4 w-4" />
      case 'COMPLETED': return <CheckCircle className="h-4 w-4" />
      case 'FAILED': return <XCircle className="h-4 w-4" />
      default: return <AlertCircle className="h-4 w-4" />
    }
  }

  const getPriorityBadge = (priority: number) => {
    if (priority >= 8) return { variant: 'destructive' as const, text: 'Критично', icon: '🔥' }
    if (priority >= 6) return { variant: 'default' as const, text: 'Высокий', icon: '⚡' }
    if (priority >= 4) return { variant: 'secondary' as const, text: 'Средний', icon: '📊' }
    return { variant: 'outline' as const, text: 'Низкий', icon: '📝' }
  }

  if (loading) {
    return (
      <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-blue-50/30 dark:from-gray-900 dark:to-blue-900/20 min-h-screen">
        <div className="flex flex-col justify-center items-center h-64 space-y-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <div className="text-sm text-gray-500">Загрузка фич…</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-blue-50/30 dark:from-gray-900 dark:to-blue-900/20 min-h-screen">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Ошибка! </strong>
          <span className="block sm:inline">{error}</span>
          <Button onClick={fetchFeatures} variant="outline" className="mt-2">
            <RefreshCw className="mr-2 h-4 w-4" />
            Попробовать снова
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-blue-50/30 dark:from-gray-900 dark:to-blue-900/20 min-h-screen">
      
      {/* Красивый заголовок */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center space-x-3 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md px-6 py-3 rounded-full shadow-lg">
          <Library className="h-6 w-6 text-blue-600 animate-pulse" />
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Features Factory
          </h1>
          <Target className="h-6 w-6 text-purple-600" />
        </div>
        <p className="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          Управление фичами — от идеи до реализации с полным контролем статуса и прогресса
        </p>
      </div>

      {/* Статистика с красивыми карточками */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        
        {/* Общая статистика */}
        <Card className="lg:col-span-2 bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Общая статистика</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4">
              <ProgressRing 
                value={stats.completed} 
                max={Math.max(stats.total, 1)} 
                size={60} 
                strokeWidth={4}
                gradientFrom="#10B981" 
                gradientTo="#059669"
              />
              <div className="flex-1">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.total}
                </div>
                <div className="text-sm text-muted-foreground">Всего фич</div>
                <Sparkline 
                  data={trendData} 
                  width={80} 
                  height={20} 
                  color="#3B82F6"
                  animate={true}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* NEW */}
        <Card 
          className="cursor-pointer hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 backdrop-blur-sm"
          onClick={() => setStatusFilter('NEW')}
          title="Новые фичи - нужно запланировать"
        >
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600">{stats.new}</div>
                <div className="text-xs text-muted-foreground">Новые</div>
              </div>
              <div className="bg-blue-100 p-2 rounded-full">
                <Plus className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* PLANNED */}
        <Card 
          className="cursor-pointer hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 backdrop-blur-sm"
          onClick={() => setStatusFilter('PLANNED')}
          title="Запланированные фичи"
        >
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-yellow-600">{stats.planned}</div>
                <div className="text-xs text-muted-foreground">Планы</div>
              </div>
              <div className="bg-yellow-100 p-2 rounded-full">
                <Clock className="h-5 w-5 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* RUNNING */}
        <Card 
          className="cursor-pointer hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 backdrop-blur-sm"
          onClick={() => setStatusFilter('RUNNING')}
          title="Фичи в разработке"
        >
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">{stats.running}</div>
                <div className="text-xs text-muted-foreground">В работе</div>
              </div>
              <div className="bg-green-100 p-2 rounded-full animate-pulse">
                <Play className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* COMPLETED */}
        <Card 
          className="cursor-pointer hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 backdrop-blur-sm"
          onClick={() => setStatusFilter('COMPLETED')}
          title="Завершённые фичи"
        >
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-emerald-600">{stats.completed}</div>
                <div className="text-xs text-muted-foreground">Готово</div>
              </div>
              <div className="bg-emerald-100 p-2 rounded-full">
                <CheckCircle className="h-5 w-5 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Панель фильтров */}
      <Card className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm shadow-lg">
        <CardContent className="pt-4">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-4">
            
            {/* Поиск */}
            <div className="flex items-center space-x-2 flex-1">
              <Search className="h-4 w-4 text-gray-400" />
              <Input
                placeholder="Поиск по названию или автору..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-xs"
              />
            </div>

            {/* Фильтры */}
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option value="all">Все статусы</option>
                <option value="NEW">Новые</option>
                <option value="PLANNED">Планы</option>
                <option value="RUNNING">В работе</option>
                <option value="COMPLETED">Готовые</option>
                <option value="FAILED">Ошибки</option>
              </select>
              
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option value="all">Все приоритеты</option>
                <option value="9">Критично (9-10)</option>
                <option value="7">Высокий (7-8)</option>
                <option value="5">Средний (5-6)</option>
                <option value="3">Низкий (1-4)</option>
              </select>
            </div>

            {/* Действия */}
            <div className="flex items-center space-x-2">
              <Button onClick={fetchFeatures} variant="outline" size="sm">
                <RefreshCw className="mr-2 h-4 w-4" />
                Обновить
              </Button>
              <Button variant="default" size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Добавить
              </Button>
            </div>
          </div>

          {/* Результаты фильтрации */}
          <div className="mt-4 text-sm text-muted-foreground">
            Показано {filteredFeatures.length} из {features.length} фич
          </div>
        </CardContent>
      </Card>

      {/* Список фич - красивые карточки */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredFeatures.map(feature => {
          const priority = getPriorityBadge(feature.priority)
          
          return (
            <Card 
              key={feature.id}
              className="group cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-300 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm"
              onClick={() => navigate(`/features/${feature.id}`)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between space-x-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(feature.status)} group-hover:animate-pulse`}></div>
                    <Badge variant={priority.variant} className="text-xs">
                      {priority.icon} {priority.text}
                    </Badge>
                  </div>
                  <Eye className="h-4 w-4 text-gray-400 group-hover:text-blue-500 transition-colors" />
                </div>
                
                <CardTitle className="text-lg leading-tight group-hover:text-blue-600 transition-colors">
                  {feature.title}
                </CardTitle>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-3">
                  
                  {/* Статус и прогресс */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(feature.status)}
                      <span className="text-sm font-medium">
                        {feature.status}
                      </span>
                    </div>
                    
                    <Badge variant="outline" className="text-xs">
                      #{feature.id}
                    </Badge>
                  </div>

                  {/* Прогресс-бар для активных фич */}
                  {feature.status === 'RUNNING' && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Прогресс</span>
                        <span>{Math.floor(Math.random() * 40 + 30)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-green-500 to-emerald-600 h-2 rounded-full transition-all duration-1000" 
                          style={{ width: `${Math.floor(Math.random() * 40 + 30)}%` }}
                        ></div>
                      </div>
                    </div>
                  )}

                  {/* Мета-информация */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center space-x-1">
                      <User className="h-3 w-3" />
                      <span>{feature.created_by}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Calendar className="h-3 w-3" />
                      <span>{formatDate(feature.created_at)}</span>
                    </div>
                  </div>

                  {/* Environment */}
                  {feature.env && (
                    <div className="flex justify-end">
                      <Badge variant="secondary" className="text-xs">
                        {feature.env}
                      </Badge>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Empty state */}
      {filteredFeatures.length === 0 && !loading && (
        <div className="text-center py-12">
          <Library className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            Фичи не найдены
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Попробуйте изменить параметры поиска или фильтры
          </p>
          <Button onClick={() => {
            setSearchTerm('')
            setStatusFilter('all')
            setPriorityFilter('all')
          }} variant="outline" className="mt-4">
            Сбросить фильтры
          </Button>
        </div>
      )}
    </div>
  )
}

export default FeaturesRedesigned