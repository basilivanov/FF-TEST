import React, { useEffect, useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { formatDate, formatRole } from '@/lib/format'
import { get } from '@/lib/api'
import Mermaid from '@/components/Mermaid'
import TaskTimeline from '@/components/TaskTimeline'
import { Sparkline } from '@/components/Sparkline'
import { ProgressRing } from '@/components/ProgressRing'
import {
  ArrowLeft,
  Activity,
  FileText,
  RefreshCw,
  Zap,
  Package,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  ExternalLink,
  Copy,
  Download,
  Eye,
  BarChart3
} from 'lucide-react'

interface Task {
  id: string
  feature_id: number
  role: string
  status: string
  attempts: number
  scheduled_at?: string | number
  started_at?: string | number
  completed_at?: string | number
  correlation_id?: string
  context_summary?: string
  progress_percentage?: number
}

interface FeatureMeta {
  id: number;
  title?: string
}

interface Artifact {
  id: string
  name: string
  type: 'file' | 'log' | 'report' | 'context' | 'output'
  size: number
  created_at: string
  url?: string
  preview?: string
}

interface TaskMetrics {
  execution_time_ms: number
  memory_usage_mb: number
  cpu_usage_percent: number
  context_tokens: number
  output_tokens: number
}

const DEFAULT_ROLES = ['Architect','Dev','QA','Scribe','Maintainer']

const TaskDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [task, setTask] = useState<Task | null>(null)
  const [feature, setFeature] = useState<FeatureMeta | null>(null)
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [metrics, setMetrics] = useState<TaskMetrics | null>(null)
  const [tab, setTab] = useState<'trace' | 'details' | 'artifacts' | 'metrics'>('trace')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    if (!id) return
    try {
      setLoading(true)
      const resp = await get<Task>(`/tasks/${id}`)
      const taskData = resp.data
      setTask(taskData)

      // Fetch related data in parallel
      const promises = []

      if (taskData?.feature_id) {
        promises.push(
          get<FeatureMeta>(`/features/${taskData.feature_id}`)
            .then(f => setFeature(f.data))
            .catch(e => console.warn('Could not fetch feature meta', e))
        )
      }

      // Mock artifacts data (in real app, would be GET /tasks/${id}/artifacts)
      promises.push(
        Promise.resolve().then(() => {
          const mockArtifacts: Artifact[] = [
            {
              id: '1',
              name: 'context.json',
              type: 'context',
              size: 15432,
              created_at: new Date(Date.now() - 60000).toISOString(),
              preview: '{"role": "' + (taskData.role || 'unknown') + '", "intent": "...", "context": {...}'
            },
            {
              id: '2',
              name: 'task_output.md',
              type: 'output',
              size: 8920,
              created_at: new Date(Date.now() - 30000).toISOString(),
              preview: '# Результат выполнения\n\n## Статус\n✅ Задача выполнена успешно...'
            },
            {
              id: '3',
              name: 'execution.log',
              type: 'log',
              size: 45231,
              created_at: new Date(Date.now() - 15000).toISOString(),
              preview: '[INFO] Starting task execution...\n[INFO] Context loaded: 15KB\n[INFO] Processing...'
            }
          ]
          setArtifacts(mockArtifacts)
        })
      )

      // Mock metrics data
      promises.push(
        Promise.resolve().then(() => {
          const mockMetrics: TaskMetrics = {
            execution_time_ms: Math.floor(Math.random() * 30000) + 5000,
            memory_usage_mb: Math.floor(Math.random() * 200) + 50,
            cpu_usage_percent: Math.floor(Math.random() * 80) + 10,
            context_tokens: Math.floor(Math.random() * 5000) + 1000,
            output_tokens: Math.floor(Math.random() * 3000) + 500
          }
          setMetrics(mockMetrics)
        })
      )

      await Promise.all(promises)
      setError(null)
    } catch (e) {
      console.error('TaskDetail: fetch error', e)
      setError('Failed to fetch task data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [id])

  const roles = DEFAULT_ROLES
  const currentRole = task?.role
  const mermaidChart = useMemo(() => {
    const nodes = roles.map(r => r).join(' --> ')
    const clsName = (currentRole && roles.includes(currentRole)) ? currentRole : ''
    const classDef = 'classDef current fill:#93c5fd,stroke:#1d4ed8,stroke-width:2px,color:#111;'
    const classApply = clsName ? `class ${clsName} current;` : ''
    const labels = roles.map(r => `${r}[${formatRole(r)}]`).join('\n')
    return `graph LR\n${labels}\n${nodes}\n${classDef}\n${classApply}`
  }, [roles, currentRole])

  const executionTimeData = useMemo(() => Array.from({length: 10}, () => Math.floor(Math.random() * 30) + 10), [metrics])
  const memoryUsageData = useMemo(() => Array.from({length: 10}, () => Math.floor(Math.random() * 200) + 50), [metrics])
  const cpuUsageData = useMemo(() => Array.from({length: 10}, () => Math.floor(Math.random() * 100)), [metrics])

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }
  if (error || !task) {
    return (
      <div className="space-y-6">
        <Button variant="outline" size="sm" asChild>
          <Link to="/tasks"><ArrowLeft className="h-4 w-4 mr-2" />Назад к задачам</Link>
        </Button>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{error || 'Задача не найдена'}</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Задача #{task.id} • {formatRole(task.role)}</h1>
          {feature && (
            <p className="text-sm text-gray-500">
              <Link to={`/admin/features/${feature.id}`} className="hover:underline">
                Фича #{feature.id} {feature.title ? `• ${feature.title}` : ''}
              </Link>
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Badge>{task.status}</Badge>
          <Button onClick={fetchData} variant="outline" size="sm"><RefreshCw className="h-4 w-4 mr-2"/>Обновить</Button>
        </div>
      </div>

      <div className="flex gap-2 text-sm border-b pb-2 overflow-x-auto">
        <Button size="sm" variant={tab === 'trace' ? 'default' : 'outline'} onClick={() => setTab('trace')}>
          <Zap className="h-4 w-4 mr-2"/>Трассировка
        </Button>
        <Button size="sm" variant={tab === 'details' ? 'default' : 'outline'} onClick={() => setTab('details')}>
          <FileText className="h-4 w-4 mr-2"/>Детали
        </Button>
        <Button size="sm" variant={tab === 'artifacts' ? 'default' : 'outline'} onClick={() => setTab('artifacts')}>
          <Package className="h-4 w-4 mr-2"/>Артефакты
        </Button>
        <Button size="sm" variant={tab === 'metrics' ? 'default' : 'outline'} onClick={() => setTab('metrics')}>
          <BarChart3 className="h-4 w-4 mr-2"/>Метрики
        </Button>
      </div>

      {tab === 'trace' && (
        <TaskTimeline taskId={task.id} />
      )}

      {tab === 'details' && (
        <div className="space-y-6">
          {/* Progress Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center"><Activity className="h-5 w-5 mr-2"/>Прогресс выполнения</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4 text-sm">Текущий шаг: {formatRole(task.role)}</div>
                <Mermaid chart={mermaidChart} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-sm"><Clock className="h-4 w-4 mr-2"/>Прогресс</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center">
                  <ProgressRing
                    value={task.progress_percentage || 0}
                    max={100}
                    size={80}
                    strokeWidth={6}
                    gradientFrom="#3B82F6"
                    gradientTo="#1E40AF"
                  />
                </div>
                <div className="text-center mt-3">
                  <div className="text-2xl font-bold text-blue-600">{task.progress_percentage || 0}%</div>
                  <div className="text-sm text-gray-500">завершено</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center"><FileText className="h-5 w-5 mr-2"/>Основные сведения</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between"><span className="text-gray-500">Роль:</span> <Badge>{formatRole(task.role)}</Badge></div>
                  <div className="flex justify-between"><span className="text-gray-500">Статус:</span> <Badge variant={task.status === 'DONE' ? 'default' : 'secondary'}>{task.status}</Badge></div>
                  <div className="flex justify-between"><span className="text-gray-500">Попытки:</span> <span>{task.attempts}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Запланировано:</span> <span>{task.scheduled_at ? formatDate(task.scheduled_at) : '—'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Начато:</span> <span>{task.started_at ? formatDate(task.started_at) : '—'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Завершено:</span> <span>{task.completed_at ? formatDate(task.completed_at) : '—'}</span></div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center"><ExternalLink className="h-5 w-5 mr-2"/>Трассировка</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {task.correlation_id && (
                    <div>
                      <label className="text-sm text-gray-500">Correlation ID</label>
                      <div className="flex items-center gap-2 mt-1">
                        <input
                          type="text"
                          value={task.correlation_id}
                          readOnly
                          className="flex-1 px-2 py-1 text-sm border rounded font-mono text-gray-700"
                        />
                        <Button size="sm" variant="outline" title="Copy ID">
                          <Copy className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="outline" title="Перейти по Correlation ID">
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  )}
                  {task.context_summary && (
                    <div>
                      <label className="text-sm text-gray-500">Контекст</label>
                      <div className="mt-1 p-2 bg-gray-50 rounded text-xs">
                        {task.context_summary}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {tab === 'artifacts' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center"><Package className="h-5 w-5 mr-2"/>Артефакты задачи</CardTitle>
            </CardHeader>
            <CardContent>
              {artifacts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Package className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Артефакты не найдены</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {artifacts.map((artifact) => (
                    <div key={artifact.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge variant={artifact.type === 'context' ? 'default' : artifact.type === 'output' ? 'secondary' : 'outline'}>
                            {artifact.type}
                          </Badge>
                          <span className="font-medium">{artifact.name}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-500">{(artifact.size / 1024).toFixed(1)} KB</span>
                          <Button size="sm" variant="outline" title="View">
                            <Eye className="h-3 w-3" />
                          </Button>
                          <Button size="sm" variant="outline" title="Download">
                            <Download className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 mb-2">
                        Создан: {formatDate(artifact.created_at)}
                      </div>
                      {artifact.preview && (
                        <div className="bg-gray-100 rounded p-2 text-xs font-mono max-h-24 overflow-hidden">
                          {artifact.preview}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {tab === 'metrics' && (
        <div className="space-y-6">
          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <Clock className="h-4 w-4" />
                  <span>Время выполнения</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {metrics ? (metrics.execution_time_ms / 1000).toFixed(1) : 0}s
                </div>
                <div className="text-sm text-gray-600">общее время</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4" />
                  <span>Использование памяти</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {metrics?.memory_usage_mb || 0} MB
                </div>
                <div className="text-sm text-gray-600">пиковое значение</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <Activity className="h-4 w-4" />
                  <span>Загрузка CPU</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">
                  {metrics?.cpu_usage_percent || 0}%
                </div>
                <div className="text-sm text-gray-600">средняя загрузка</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <ProgressRing
                    value={task.progress_percentage || 0}
                    max={100}
                    size={20}
                    strokeWidth={2}
                    gradientFrom="#10B981"
                    gradientTo="#059669"
                  />
                  <span>Прогресс</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-emerald-600">
                  {task.progress_percentage || 0}%
                </div>
                <div className="text-sm text-gray-600">завершено</div>
              </CardContent>
            </Card>
          </div>

          {/* Token Usage */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="h-5 w-5 mr-2"/>
                  Использование токенов
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Токены контекста</span>
                    <span className="font-medium">{metrics?.context_tokens || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Токены вывода</span>
                    <span className="font-medium">{metrics?.output_tokens || 0}</span>
                  </div>
                  <div className="flex justify-between items-center border-t pt-2">
                    <span className="text-sm font-medium">Всего токенов</span>
                    <span className="font-bold">{(metrics?.context_tokens || 0) + (metrics?.output_tokens || 0)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2"/>
                  Тенденция производительности
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="text-sm text-gray-600">Время выполнения за последние запуски</div>
                  <Sparkline
                    data={executionTimeData}
                    width={200}
                    height={50}
                    color="#3B82F6"
                    animate={true}
                  />
                  <div className="text-xs text-gray-500">Последние 10 выполнений</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}

export default TaskDetail
