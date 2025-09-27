import React from 'react'
import { Card } from '@/shadcn/ui/card'
import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

interface GlassCardProps extends CardProps {
  children: React.ReactNode
  variant?: 'default' | 'glass' | 'gradient' | 'neon'
  intensity?: 'low' | 'medium' | 'high'
  hover?: boolean
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  variant = 'glass',
  intensity = 'medium',
  hover = true,
  ...props
}) => {
  const baseClasses = "relative overflow-hidden transition-all duration-300"
  
  const variantClasses = {
    default: "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
    glass: cn(
      "backdrop-blur-md border border-white/20 dark:border-white/10",
      intensity === 'low' && "bg-white/70 dark:bg-gray-900/70",
      intensity === 'medium' && "bg-white/80 dark:bg-gray-900/80", 
      intensity === 'high' && "bg-white/90 dark:bg-gray-900/90"
    ),
    gradient: "bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 border border-gray-200/50 dark:border-gray-700/50",
    neon: "bg-gray-900/95 border border-cyan-400/30 shadow-lg shadow-cyan-400/20"
  }
  
  const hoverClasses = hover ? cn(
    "hover:scale-[1.02] hover:shadow-xl",
    variant === 'glass' && "hover:bg-white/85 dark:hover:bg-gray-900/85",
    variant === 'neon' && "hover:border-cyan-400/50 hover:shadow-cyan-400/40"
  ) : ""

  return (
    <Card 
      className={cn(
        baseClasses,
        variantClasses[variant],
        hoverClasses,
        className
      )}
      {...props}
    >
      {/* Декоративные элементы для neon варианта */}
      {variant === 'neon' && (
        <>
          <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-50" />
          <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-50" />
        </>
      )}
      
      {/* Gradient overlay для gradient варианта */}
      {variant === 'gradient' && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-600/5 pointer-events-none" />
      )}
      
      {children}
    </Card>
  )
}