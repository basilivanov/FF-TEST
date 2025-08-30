import React, { useState, useEffect } from 'react'
import { get } from '@/lib/api'

interface TraceEvent {
  timestamp: string
  kind: string
  icon: string
  title: string
  description: string
  severity: 'info' | 'warn' | 'error'
  links: {
    log_id?: string
    artifact?: string
  }
  details: Record<string, any>
}

interface TraceResponse {
  task_id: string
  items: TraceEvent[]
  total: number
}

interface TaskTimelineProps {
  taskId: string
}

const TaskTimeline: React.FC<TaskTimelineProps> = ({ taskId }) => {
  const [events, setEvents] = useState<TraceEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedEvent, setExpandedEvent] = useState<number | null>(null)

  useEffect(() => {
    const fetchTaskTrace = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await get<TraceResponse>(`/tasks/${taskId}/trace?limit=50`)
        setEvents(response.data.items)
      } catch (err: any) {
        setError(err?.response?.data?.detail || err?.message || 'Ошибка загрузки trace')
      } finally {
        setLoading(false)
      }
    }

    if (taskId) {
      fetchTaskTrace()
    }
  }, [taskId])

  const handleOpenLog = (logId: string) => {
    window.open(`/admin/logs?corr=${logId}`, '_blank')
  }

  const handleShowArtifact = (artifactPath: string) => {
    window.open(artifactPath, '_blank')
  }

  const toggleEventDetails = (eventId: number) => {
    setExpandedEvent(expandedEvent === eventId ? null : eventId)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'info': return 'bg-green-500'
      case 'warn': return 'bg-yellow-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex animate-pulse">
            <div className="flex flex-col items-center mr-4">
              <div className="w-4 h-4 bg-gray-300 rounded-full"></div>
              <div className="w-0.5 h-full bg-gray-300"></div>
            </div>
            <div className="flex-1 pb-4">
              <div className="h-4 bg-gray-300 rounded w-1/4 mb-2"></div>
              <div className="h-3 bg-gray-300 rounded w-3/4"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <h3 className="ml-2 text-sm font-medium text-red-800">Ошибка загрузки трассировки</h3>
        </div>
        <div className="mt-2 text-sm text-red-700">
          <p>{error}</p>
        </div>
        <div className="mt-4">
          <button
            type="button"
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            onClick={() => window.location.reload()}
          >
            Повторить
          </button>
        </div>
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-8">
        <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">Событий пока нет</h3>
        <p className="mt-1 text-sm text-gray-500">Проверьте, что задача запущена.</p>
      </div>
    )
  }

  return (
    <div className="flow-root">
      <ul className="relative border-l border-gray-200">
        {events.map((event, index) => (
          <li key={index} className="mb-4 ml-6">
            <div className="absolute -left-3 flex items-center justify-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${getSeverityColor(event.severity)}`}>
                <span className="text-white text-xs">{event.icon}</span>
              </div>
            </div>
            <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center mb-1">
                    <span className="text-xs font-normal text-gray-500 mr-2">
                      {new Date(event.timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                    <span 
                      className="text-xs font-normal text-gray-500 cursor-help"
                      title={new Date(event.timestamp).toLocaleString('ru-RU')}
                    >
                      📅
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900 flex items-center">
                    {event.title}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1 truncate">
                    {event.description}
                  </p>
                </div>
                <div className="flex space-x-2">
                  {event.links.log_id && (
                    <button
                      onClick={() => handleOpenLog(event.links.log_id!)}
                      className="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Открыть лог
                    </button>
                  )}
                  {event.links.artifact && (
                    <button
                      onClick={() => handleShowArtifact(event.links.artifact!)}
                      className="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Показать артефакт
                    </button>
                  )}
                </div>
              </div>
              <div className="mt-3">
                <button
                  onClick={() => toggleEventDetails(index)}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-500"
                >
                  {expandedEvent === index ? 'Скрыть детали' : 'Показать детали'}
                </button>
                {expandedEvent === index && (
                  <div className="mt-2 p-3 bg-gray-50 rounded-md">
                    <pre className="text-xs text-gray-700 overflow-x-auto">
                      {JSON.stringify(event.details, null, 2)}
                    </pre>
                    <button
                      onClick={() => navigator.clipboard.writeText(JSON.stringify(event.details, null, 2))}
                      className="mt-2 inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Копировать
                    </button>
                  </div>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default TaskTimeline