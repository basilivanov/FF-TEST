import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

// Определяем варианты для StatusPill с помощью class-variance-authority
const statusPillVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100',
        secondary: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100',
        success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100',
        destructive: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100',
        warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100',
        outline: 'border border-gray-200 text-gray-800 dark:border-gray-700 dark:text-gray-100',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

// Типы для props компонента
export interface StatusPillProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusPillVariants> {
  icon?: React.ReactNode
}

// Компонент StatusPill
const StatusPill = React.forwardRef<HTMLSpanElement, StatusPillProps>(
  ({ className, variant, icon, children, ...props }, ref) => {
    return (
      <span
        className={cn(statusPillVariants({ variant }), className)}
        ref={ref}
        {...props}
      >
        {icon && <span className="mr-1.5">{icon}</span>}
        {children}
      </span>
    )
  }
)

StatusPill.displayName = 'StatusPill'

export { StatusPill, statusPillVariants }