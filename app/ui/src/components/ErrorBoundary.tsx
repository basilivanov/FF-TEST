import React from 'react'
import { Button } from '@/shadcn/ui/button'
import { AlertTriangle, RefreshCw, FileText } from 'lucide-react'
import { reportClientError } from '@/lib/clientLog'

type Props = { children: React.ReactNode }
type State = { hasError: boolean; error?: any }

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: any) {
    return { hasError: true, error }
  }

  componentDidCatch(error: any, info: any) {
    reportClientError({
      message: String(error?.message || error || 'UI Error'),
      stack: String(error?.stack || ''),
      extra: { componentStack: info?.componentStack },
    }).catch(() => void 0)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-2xl mx-auto mt-16 p-6 border rounded-lg bg-red-50 dark:bg-red-900/20">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300 mb-2">
            <AlertTriangle className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Произошла ошибка в интерфейсе</h2>
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">Мы зафиксировали событие и разберёмся. Вы можете обновить страницу или открыть логи.</p>
          <div className="flex gap-2">
            <Button onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4 mr-2" />Обновить страницу
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                try {
                  const p = window.location.pathname || '/'
                  const base = p.startsWith('/admin') ? '/admin' : ''
                  window.location.assign(`${base}/logs`)
                } catch {
                  window.location.assign('/logs')
                }
              }}
            >
              <FileText className="h-4 w-4 mr-2" />Открыть логи
            </Button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
