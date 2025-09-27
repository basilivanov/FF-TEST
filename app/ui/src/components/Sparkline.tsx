import React from 'react'

interface SparklineDataPoint {
  value: number
  timestamp?: string
}

interface SparklineProps {
  data: SparklineDataPoint[] | number[]
  width?: number
  height?: number
  className?: string
  color?: string
  fillColor?: string
  showDots?: boolean
  showArea?: boolean
  animate?: boolean
  strokeWidth?: number
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  width = 120,
  height = 40,
  className = '',
  color = '#3B82F6',
  fillColor = 'rgba(59, 130, 246, 0.1)',
  showDots = false,
  showArea = true,
  animate = true,
  strokeWidth = 2
}) => {
  if (!data || data.length === 0) {
    return (
      <div
        className={`flex items-center justify-center ${className}`}
        style={{ width, height }}
        data-testid="sparkline-empty"
      >
        <div className="text-xs text-gray-400">Нет данных</div>
      </div>
    )
  }

  // Normalize data to array of numbers
  const values = data.map(item => typeof item === 'number' ? item : item.value)

  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = max - min || 1

  const points = values.map((value, index) => ({
    x: values.length === 1 ? width / 2 : (index / (values.length - 1)) * width,
    y: height - ((value - min) / range) * height
  }))

  const pathData = points.reduce((acc, point, index) => {
    const command = index === 0 ? 'M' : 'L'
    return `${acc} ${command} ${point.x} ${point.y}`
  }, '')

  const fillPathData = `${pathData} L ${width} ${height} L 0 ${height} Z`

  const pathLength = points.length > 1 ? 
    points.reduce((acc, point, index) => {
      if (index === 0) return 0
      const prev = points[index - 1]
      return acc + Math.sqrt(Math.pow(point.x - prev.x, 2) + Math.pow(point.y - prev.y, 2))
    }, 0) : 0

  return (
    <div className={`relative ${className}`}>
      <svg
        width={width}
        height={height}
        className="overflow-visible"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        data-testid="sparkline-svg"
      >
        <defs>
          <linearGradient id="sparklineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.05" />
          </linearGradient>
        </defs>

        {/* Заливка области */}
        {showArea && (
          <path
            d={fillPathData}
            fill="url(#sparklineGradient)"
            className={animate ? "animate-pulse" : ""}
            data-testid="sparkline-area"
          />
        )}

        {/* Основная линия */}
        {points.length > 1 && (
          <path
            d={pathData}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="transition-all duration-300"
            style={animate ? {
              strokeDasharray: pathLength,
              strokeDashoffset: pathLength,
              animation: 'drawLine 1.5s ease-out forwards'
            } : {}}
            data-testid="sparkline-path"
          />
        )}

        {/* Точки на линии */}
        {showDots && points.map((point, index) => (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r="2"
            fill={color}
            className={animate ? "animate-bounce" : ""}
            style={animate ? { animationDelay: `${index * 0.1}s` } : {}}
            data-testid={`sparkline-dot-${index}`}
          />
        ))}

        {/* Последняя точка с пульсацией */}
        {points.length > 0 && (
          <circle
            cx={points[points.length - 1].x}
            cy={points[points.length - 1].y}
            r="3"
            fill={color}
            className="animate-pulse"
            data-testid="sparkline-last-point"
          />
        )}
      </svg>
    </div>
  )
}