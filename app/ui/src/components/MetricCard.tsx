import React from 'react'
import { GlassCard } from './GlassCard'
import { CardHeader, CardContent } from '@/shadcn/ui/card'
import { ProgressRing } from './ProgressRing'
import { Sparkline } from './Sparkline'
import { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: LucideIcon
  trend?: number[]
  progress?: { value: number; max: number; label?: string }
  variant?: 'default' | 'glass' | 'gradient' | 'neon'
  status?: 'success' | 'warning' | 'error' | 'neutral'
  onClick?: () => void
  children?: React.ReactNode
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  progress,
  variant = 'glass',
  status = 'neutral',
  onClick,
  children
}) => {
  const statusColors = {
    success: { primary: '#10B981', secondary: '#D1FAE5', accent: '#047857' },
    warning: { primary: '#F59E0B', secondary: '#FEF3C7', accent: '#D97706' },
    error: { primary: '#EF4444', secondary: '#FEE2E2', accent: '#DC2626' },
    neutral: { primary: '#6B7280', secondary: '#F3F4F6', accent: '#374151' }
  }

  const colors = statusColors[status]

  return (
    <GlassCard 
      variant={variant}
      className={onClick ? "cursor-pointer" : ""}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center space-x-2">
          {Icon && (
            <div 
              className="p-2 rounded-lg"
              style={{ backgroundColor: colors.secondary }}
            >
              <Icon 
                className="h-4 w-4" 
                style={{ color: colors.accent }}
              />
            </div>
          )}
          <div>
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-300">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        
        {/* Индикатор статуса */}
        <div 
          className="w-3 h-3 rounded-full animate-pulse"
          style={{ backgroundColor: colors.primary }}
        />
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {/* Основное значение */}
          <div className="flex items-end justify-between">
            <div>
              <div 
                className="text-3xl font-bold"
                style={{ color: colors.accent }}
              >
                {value}
              </div>
              {trend && (
                <div className="flex items-center space-x-2 mt-1">
                  <Sparkline 
                    data={trend}
                    width={60}
                    height={20}
                    color={colors.primary}
                    showDots={false}
                    animate={true}
                  />
                  <span className="text-xs text-gray-500">
                    Тренд
                  </span>
                </div>
              )}
            </div>
            
            {/* Прогресс-кольцо */}
            {progress && (
              <ProgressRing
                value={progress.value}
                max={progress.max}
                size={80}
                strokeWidth={6}
                gradientFrom={colors.primary}
                gradientTo={colors.accent}
                labelText={progress.label}
                showLabel={true}
              />
            )}
          </div>
          
          {/* Дополнительный контент */}
          {children}
        </div>
      </CardContent>
    </GlassCard>
  )
}