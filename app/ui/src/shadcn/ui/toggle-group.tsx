import * as React from "react"
import { cn } from "@/shadcn/lib/utils"

interface ToggleGroupOption {
  value: string
  label: string
  icon?: React.ReactNode
}

interface ToggleGroupProps {
  options: ToggleGroupOption[]
  value: string
  onValueChange: (value: string) => void
  className?: string
}

export const ToggleGroup: React.FC<ToggleGroupProps> = ({
  options,
  value,
  onValueChange,
  className
}) => {
  return (
    <div className={cn("inline-flex rounded-md bg-muted p-1", className)}>
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onValueChange(option.value)}
          className={cn(
            "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
            value === option.value
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:bg-background/50 hover:text-foreground"
          )}
          type="button"
        >
          {option.icon && <span className="mr-2">{option.icon}</span>}
          {option.label}
        </button>
      ))}
    </div>
  )
}