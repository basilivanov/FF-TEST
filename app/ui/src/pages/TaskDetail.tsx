import React, { useEffect, useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { formatDate, formatRole } from '@/lib/format'
import { get } from '@/lib/api'
import Mermaid from '@/components/Mermaid'
import TaskTimeline from '@/components/TaskTimeline'
import { ArrowLeft, Activity, FileText, RefreshCw, Zap } from 'lucide-react'

interface Task {
  id: string
  feature_id: number
  role: string
  status: string
  attempts: number
  scheduled_at?: string | number
  started_at?: string | number
}

interface FeatureMeta { id: number; title?: string }

const DEFAULT_ROLES = ['Architect','Dev','QA','Scribe','Maintainer']

const TaskDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [task, setTask] = useState<Task | null>(null)
  const [feature, setFeature] = useState<FeatureMeta | null>(null)
  const [tab, setTab] = useState<'trace' | 'details'>('trace')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    if (!id) return
    try {
      setLoading(true)
      const resp = await get<Task>(`/tasks/${id}`)
      const taskData = resp.data
      setTask(taskData)

      if (taskData?.feature_id) {
        try {
          const f = await get<FeatureMeta>(`/features/${taskData.feature_id}`)
          setFeature(f.data)
        } catch (e) {
          console.warn('Could not fetch feature meta', e)
        }
      }
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

      <div className="flex gap-2 text-sm border-b pb-2">
        <Button size="sm" variant={tab === 'trace' ? 'default' : 'outline'} onClick={() => setTab('trace')}> <Zap className="h-4 w-4 mr-2"/>Трассировка выполнения</Button>
        <Button size="sm" variant={tab === 'details' ? 'default' : 'outline'} onClick={() => setTab('details')}> <FileText className="h-4 w-4 mr-2"/>Детали</Button>
      </div>

      {tab === 'trace' && (
        <TaskTimeline taskId={task.id} />
      )}

      {tab === 'details' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center"><Activity className="h-5 w-5 mr-2"/>Прогресс</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-2 text-sm">Текущий шаг: {formatRole(task.role)}</div>
              <Mermaid chart={mermaidChart} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center"><FileText className="h-5 w-5 mr-2"/>Сведения</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div><span className="text-gray-500">Роль:</span> {formatRole(task.role)}</div>
                <div><span className="text-gray-500">Попытки:</span> {task.attempts}</div>
                <div><span className="text-gray-500">Запланировано:</span> {task.scheduled_at ? formatDate(task.scheduled_at) : '—'}</div>
                <div><span className="text-gray-500">Начато:</span> {task.started_at ? formatDate(task.started_at) : '—'}</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default TaskDetail
