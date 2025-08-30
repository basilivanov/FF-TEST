import React, { useEffect, useState } from 'react'
import { XCircle, AlertTriangle } from 'lucide-react'
import { Button } from '@/shadcn/ui/button'

type AlertItem = {
  id: string
  kind: 'api' | 'sse'
  message: string
  meta?: any
}

const AlertBar: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([])

  useEffect(() => {
    const onApiError = (e: Event) => {
      const detail = (e as CustomEvent).detail || {}
      const msg = `Ошибка API${detail.status ? ` (${detail.status})` : ''}: ${detail.url || ''}`
      setAlerts((prev) => [{ id: crypto.randomUUID(), kind: 'api', message: msg, meta: detail }, ...prev].slice(0, 5))
    }
    const onSseError = (e: Event) => {
      const detail = (e as CustomEvent).detail || {}
      const msg = 'SSE: Реал‑тайм соединение разорвано'
      setAlerts((prev) => [{ id: crypto.randomUUID(), kind: 'sse', message: msg, meta: detail }, ...prev].slice(0, 5))
    }
    window.addEventListener('ff-api-error', onApiError as EventListener)
    window.addEventListener('ff-sse-error', onSseError as EventListener)
    return () => {
      window.removeEventListener('ff-api-error', onApiError as EventListener)
      window.removeEventListener('ff-sse-error', onSseError as EventListener)
    }
  }, [])

  const dismiss = (id: string) => setAlerts((prev) => prev.filter(a => a.id !== id))

  if (alerts.length === 0) return null

  return (
    <div className="p-2 space-y-2">
      {alerts.map((a) => (
        <div key={a.id} className={`flex items-center justify-between px-3 py-2 rounded border ${a.kind === 'api' ? 'bg-red-100 border-red-300 text-red-800' : 'bg-yellow-100 border-yellow-300 text-yellow-900'}`}>
          <div className="flex items-center">
            {a.kind === 'api' ? <XCircle className="h-4 w-4 mr-2"/> : <AlertTriangle className="h-4 w-4 mr-2"/>}
            <span className="text-sm">{a.message}</span>
          </div>
          <Button size="sm" variant="outline" onClick={() => dismiss(a.id)}>Закрыть</Button>
        </div>
      ))}
    </div>
  )
}

export default AlertBar

