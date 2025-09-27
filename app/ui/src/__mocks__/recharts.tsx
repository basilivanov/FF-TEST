import React from 'react'

// Mock Recharts components
export const ResponsiveContainer = ({ children }: any) => (
  <div data-testid="recharts-container" className="recharts-wrapper">
    {children}
  </div>
)

export const AreaChart = ({ children }: any) => (
  <div data-testid="area-chart">{children}</div>
)

export const Area = () => <div data-testid="area" />

export const BarChart = ({ children }: any) => (
  <div data-testid="bar-chart">{children}</div>
)

export const Bar = () => <div data-testid="bar" />

export const PieChart = ({ children }: any) => (
  <div data-testid="pie-chart">{children}</div>
)

export const Pie = () => <div data-testid="pie" />

export const LineChart = ({ children }: any) => (
  <div data-testid="line-chart">{children}</div>
)

export const Line = () => <div data-testid="line" />

export const XAxis = () => <div data-testid="x-axis" />

export const YAxis = () => <div data-testid="y-axis" />

export const CartesianGrid = () => <div data-testid="cartesian-grid" />

export const Tooltip = () => <div data-testid="tooltip" />

export const Cell = () => <div data-testid="cell" />