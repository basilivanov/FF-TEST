import React from 'react'
import { ProgressRing } from './ProgressRing'

interface HealthMetric {
  name: string
  value: number
  max: number
  status: 'healthy' | 'warning' | 'critical'
}

interface SystemHealthRadialProps {
  metrics: HealthMetric[]
  overallHealth: number
  className?: string
}

export const SystemHealthRadial: React.FC<SystemHealthRadialProps> = ({
  metrics,
  overallHealth,
  className = ''
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return { from: '#10B981', to: '#047857' }
      case 'warning': return { from: '#F59E0B', to: '#D97706' }
      case 'critical': return { from: '#EF4444', to: '#DC2626' }
      default: return { from: '#6B7280', to: '#374151' }
    }
  }

  const overallStatus = overallHealth > 90 ? 'healthy' : overallHealth > 70 ? 'warning' : 'critical'
  const overallColors = getStatusColor(overallStatus)

  return (
    <div className={`flex flex-col items-center space-y-6 ${className}`} data-testid="system-health-radial">
      {/* Основное кольцо здоровья системы */}
      <div className="relative">
        <ProgressRing
          value={overallHealth}
          max={100}
          size={160}
          strokeWidth={12}
          gradientFrom={overallColors.from}
          gradientTo={overallColors.to}
          labelText="Общее здоровье"
          data-testid="overall-health-ring"
        />
        
        {/* Пульсирующий эффект для критических состояний */}
        {overallStatus === 'critical' && (
          <div className="absolute inset-0 rounded-full animate-ping bg-red-400 opacity-20" />
        )}
      </div>

      {/* Мини-кольца для отдельных метрик */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full">
        {metrics.map((metric, index) => {
          const colors = getStatusColor(metric.status)
          return (
            <div key={metric.name} className="flex flex-col items-center space-y-2">
              <ProgressRing
                value={metric.value}
                max={metric.max}
                size={60}
                strokeWidth={4}
                gradientFrom={colors.from}
                gradientTo={colors.to}
                showLabel={false}
                data-testid={`metric-ring-${index}`}
              />
              <div className="text-center">
                <div className="text-xs font-medium text-gray-900 dark:text-white">
                  {metric.name}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {metric.value}/{metric.max}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Легенда статусов */}
      <div className="flex items-center space-x-4 text-xs">
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-gray-600 dark:text-gray-400">Здорово</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 rounded-full bg-yellow-500" />
          <span className="text-gray-600 dark:text-gray-400">Предупреждение</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 rounded-full bg-red-500" />
          <span className="text-gray-600 dark:text-gray-400">Критично</span>
        </div>
      </div>
    </div>
  )
}