import React, { useMemo } from 'react'
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import {
  Activity,
  BarChart3,
  PieChart as PieChartIcon,
  TrendingUp,
  Zap,
  AlertTriangle,
  Info,
  CheckCircle
} from 'lucide-react'
import { Sparkline } from '@/components/Sparkline'

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

interface LogsChartsProps {
  logs: LogEntry[]
  liveTail: boolean
}

const LEVEL_COLORS = {
  DEBUG: '#3B82F6',
  INFO: '#10B981',
  WARN: '#F59E0B',
  ERROR: '#EF4444',
  FATAL: '#991B1B'
}

const LogsCharts: React.FC<LogsChartsProps> = ({ logs, liveTail }) => {

  // Группировка логов по времени (по часам)
  const timeDistribution = useMemo(() => {
    const hourBuckets: Record<string, Record<string, number>> = {}

    logs.forEach(log => {
      const date = new Date(log.timestamp)
      const hour = date.getHours()
      const hourKey = `${hour.toString().padStart(2, '0')}:00`

      if (!hourBuckets[hourKey]) {
        hourBuckets[hourKey] = { DEBUG: 0, INFO: 0, WARN: 0, ERROR: 0, FATAL: 0 }
      }
      hourBuckets[hourKey][log.level]++
    })

    return Object.entries(hourBuckets)
      .map(([hour, levels]) => ({
        hour,
        ...levels,
        total: Object.values(levels).reduce((sum, count) => sum + count, 0)
      }))
      .sort((a, b) => a.hour.localeCompare(b.hour))
  }, [logs])

  // Группировка по уровням
  const levelDistribution = useMemo(() => {
    const levels: Record<string, number> = {}
    logs.forEach(log => {
      levels[log.level] = (levels[log.level] || 0) + 1
    })

    return Object.entries(levels).map(([level, count]) => ({
      level,
      count,
      color: LEVEL_COLORS[level as keyof typeof LEVEL_COLORS]
    }))
  }, [logs])

  // Топ сервисов
  const topServices = useMemo(() => {
    const services: Record<string, number> = {}
    logs.forEach(log => {
      services[log.service] = (services[log.service] || 0) + 1
    })

    return Object.entries(services)
      .map(([service, count]) => ({ service, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  }, [logs])

  // Тренд за последние 24 часа (по часам)
  const hourlyTrend = useMemo(() => {
    const now = new Date()
    const hourlyData = []

    for (let i = 23; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000)
      const hourStart = hour.getHours()

      const hourLogs = logs.filter(log => {
        const logHour = new Date(log.timestamp).getHours()
        return logHour === hourStart
      })

      hourlyData.push({
        hour: `${hourStart.toString().padStart(2, '0')}h`,
        count: hourLogs.length,
        errors: hourLogs.filter(l => l.level === 'ERROR' || l.level === 'FATAL').length
      })
    }

    return hourlyData
  }, [logs])

  // Статистика по ошибкам
  const errorStats = useMemo(() => {
    const errorLogs = logs.filter(log => log.level === 'ERROR' || log.level === 'FATAL')
    const warnLogs = logs.filter(log => log.level === 'WARN')
    const totalErrors = errorLogs.length
    const totalWarnings = warnLogs.length
    const errorRate = logs.length > 0 ? (totalErrors / logs.length) * 100 : 0

    return {
      totalErrors,
      totalWarnings,
      errorRate,
      recentErrors: errorLogs.slice(0, 5)
    }
  }, [logs])

  // Данные для sparkline активности
  const activitySparkData = useMemo(() => {
    const data = []
    for (let i = 0; i < 20; i++) {
      const value = Math.floor(Math.random() * 50) + 10
      data.push(value)
    }
    return data
  }, [liveTail]) // Обновляется при изменении liveTail

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border">
          <p className="font-medium">{`${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.dataKey}: ${entry.value}`}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-6">

      {/* Статистика в карточках */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        {/* Общая активность */}
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">{logs.length}</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">Всего логов</div>
                <Sparkline
                  data={activitySparkData}
                  width={80}
                  height={20}
                  color="#3B82F6"
                  animate={liveTail}
                />
              </div>
              <div className="bg-blue-200 dark:bg-blue-800 p-2 rounded-full">
                <Activity className="h-5 w-5 text-blue-600 dark:text-blue-300" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Ошибки */}
        <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-red-700 dark:text-red-300">{errorStats.totalErrors}</div>
                <div className="text-xs text-red-600 dark:text-red-400">Критичные ошибки</div>
                <div className="text-xs text-red-500 mt-1">
                  {errorStats.errorRate.toFixed(1)}% от всех логов
                </div>
              </div>
              <div className="bg-red-200 dark:bg-red-800 p-2 rounded-full">
                <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-300" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Предупреждения */}
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">{errorStats.totalWarnings}</div>
                <div className="text-xs text-yellow-600 dark:text-yellow-400">Предупреждения</div>
                <div className="text-xs text-yellow-500 mt-1">
                  Требуют внимания
                </div>
              </div>
              <div className="bg-yellow-200 dark:bg-yellow-800 p-2 rounded-full">
                <Zap className="h-5 w-5 text-yellow-600 dark:text-yellow-300" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Успешные операции */}
        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                  {logs.filter(l => l.level === 'INFO' || l.level === 'DEBUG').length}
                </div>
                <div className="text-xs text-green-600 dark:text-green-400">Успешно</div>
                <div className="text-xs text-green-500 mt-1">
                  Нормальная работа
                </div>
              </div>
              <div className="bg-green-200 dark:bg-green-800 p-2 rounded-full">
                <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-300" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Тренд активности по часам */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <TrendingUp className="h-4 w-4" />
              <span>Активность по часам</span>
            </CardTitle>
            {liveTail && <Badge variant="default" className="text-xs animate-pulse">LIVE</Badge>}
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={hourlyTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="hour" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#3B82F6"
                  fill="url(#colorCount)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="errors"
                  stroke="#EF4444"
                  fill="url(#colorErrors)"
                  strokeWidth={2}
                />
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                  </linearGradient>
                  <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Распределение по уровням */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <PieChartIcon className="h-4 w-4" />
              <span>Распределение по уровням</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4">
              <ResponsiveContainer width="60%" height={200}>
                <PieChart>
                  <Pie
                    data={levelDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="count"
                  >
                    {levelDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-2">
                {levelDistribution.map((entry) => (
                  <div key={entry.level} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: entry.color }}
                      />
                      <span className="text-sm font-medium">{entry.level}</span>
                    </div>
                    <span className="text-sm text-gray-600 dark:text-gray-300">{entry.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Дополнительные графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Топ сервисов */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Активность по сервисам</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={topServices.slice(0, 8)} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" fontSize={12} />
                <YAxis type="category" dataKey="service" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Временное распределение (детальное) */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Activity className="h-4 w-4" />
              <span>Распределение по времени</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={timeDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="hour" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="INFO"
                  stackId="1"
                  stroke={LEVEL_COLORS.INFO}
                  fill={LEVEL_COLORS.INFO}
                  fillOpacity={0.8}
                />
                <Area
                  type="monotone"
                  dataKey="WARN"
                  stackId="1"
                  stroke={LEVEL_COLORS.WARN}
                  fill={LEVEL_COLORS.WARN}
                  fillOpacity={0.8}
                />
                <Area
                  type="monotone"
                  dataKey="ERROR"
                  stackId="1"
                  stroke={LEVEL_COLORS.ERROR}
                  fill={LEVEL_COLORS.ERROR}
                  fillOpacity={0.8}
                />
                <Area
                  type="monotone"
                  dataKey="DEBUG"
                  stackId="1"
                  stroke={LEVEL_COLORS.DEBUG}
                  fill={LEVEL_COLORS.DEBUG}
                  fillOpacity={0.8}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Последние критичные ошибки */}
      {errorStats.recentErrors.length > 0 && (
        <Card className="border-red-200 dark:border-red-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2 text-red-700 dark:text-red-300">
              <AlertTriangle className="h-4 w-4" />
              <span>Последние критичные ошибки</span>
            </CardTitle>
            <Badge variant="destructive" className="text-xs">
              {errorStats.recentErrors.length}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {errorStats.recentErrors.map((error, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <Badge variant="destructive" className="text-xs">{error.level}</Badge>
                      <Badge variant="outline" className="text-xs">{error.service}</Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(error.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 truncate">
                      {error.message}
                    </p>
                    {error.correlation_id && (
                      <p className="text-xs text-blue-600 dark:text-blue-400 font-mono mt-1">
                        ID: {error.correlation_id}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default LogsCharts