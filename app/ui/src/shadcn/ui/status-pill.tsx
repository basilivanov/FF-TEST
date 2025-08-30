import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

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
        outline: 'border border-gray-200 bg-transparent text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface StatusPillProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusPillVariants> {}

function StatusPill({ className, variant, ...props }: StatusPillProps) {
  return (
    <span className={cn(statusPillVariants({ variant }), className)} {...props} />
  )
}

export { StatusPill, statusPillVariants }