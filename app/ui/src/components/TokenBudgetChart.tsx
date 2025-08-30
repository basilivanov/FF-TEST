import React from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

interface TokenStats {
  role: string
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost: number
  daily_limit: number
  daily_used: number
  daily_remaining: number
}

interface BudgetSummary {
  total_daily_limit: number
  total_daily_used: number
  total_daily_remaining: number
  roles_summary: Record<string, {
    daily_limit: number
    daily_used: number
    daily_remaining: number
    percentage_used: number
  }>
}

interface TokenBudgetChartProps {
  tokenStats: TokenStats[]
  budgetSummary: BudgetSummary
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

const TokenBudgetChart: React.FC<TokenBudgetChartProps> = ({ tokenStats, budgetSummary }) => {
  // Prepare data for bar chart
  const barChartData = tokenStats.map(stat => ({
    name: `${stat.role} (${stat.model})`,
    input: stat.input_tokens,
    output: stat.output_tokens,
    total: stat.total_tokens,
    limit: stat.daily_limit,
    used: stat.daily_used,
    remaining: stat.daily_remaining
  }))

  // Prepare data for pie chart
  const pieChartData = Object.entries(budgetSummary.roles_summary).map(([role, summary]) => ({
    name: role,
    value: summary.daily_used,
    limit: summary.daily_limit,
    percentage: summary.percentage_used
  }))

  // Calculate overall usage percentage
  const overallPercentage = budgetSummary.total_daily_limit > 0 
    ? (budgetSummary.total_daily_used / budgetSummary.total_daily_limit) * 100 
    : 0

  return (
    <div className="space-y-6">
      {/* Overall Budget Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Общий лимит</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {budgetSummary.total_daily_limit.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">токенов в день</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Использовано</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {budgetSummary.total_daily_used.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">токенов сегодня</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Осталось</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {budgetSummary.total_daily_remaining.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {overallPercentage.toFixed(1)}% использовано
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Использование токенов по ролям и моделям</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={barChartData}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 60,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45} 
                  textAnchor="end" 
                  height={60}
                />
                <YAxis />
                <Tooltip 
                  formatter={(value) => [value.toLocaleString(), 'Токены']}
                  labelFormatter={(value) => `Роль/Модель: ${value}`}
                />
                <Legend />
                <Bar dataKey="input" fill="#8884d8" name="Входные токены" />
                <Bar dataKey="output" fill="#82ca9d" name="Выходные токены" />
                <Bar dataKey="total" fill="#ffc658" name="Всего токенов" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Распределение по ролям</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="name"
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [value.toLocaleString(), 'Токены']}
                  labelFormatter={(value) => `Роль: ${value}`}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Stats Table */}
      <Card>
        <CardHeader>
          <CardTitle>Детализация по ролям и моделям</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Роль</th>
                  <th className="text-left py-2">Модель</th>
                  <th className="text-right py-2">Входные</th>
                  <th className="text-right py-2">Выходные</th>
                  <th className="text-right py-2">Всего</th>
                  <th className="text-right py-2">Лимит</th>
                  <th className="text-right py-2">Использовано</th>
                  <th className="text-right py-2">Осталось</th>
                  <th className="text-right py-2">%</th>
                </tr>
              </thead>
              <tbody>
                {tokenStats.map((stat, index) => (
                  <tr key={index} className="border-b">
                    <td className="py-2">{stat.role}</td>
                    <td className="py-2">{stat.model}</td>
                    <td className="text-right py-2">{stat.input_tokens.toLocaleString()}</td>
                    <td className="text-right py-2">{stat.output_tokens.toLocaleString()}</td>
                    <td className="text-right py-2">{stat.total_tokens.toLocaleString()}</td>
                    <td className="text-right py-2">{stat.daily_limit.toLocaleString()}</td>
                    <td className="text-right py-2">{stat.daily_used.toLocaleString()}</td>
                    <td className="text-right py-2">{stat.daily_remaining.toLocaleString()}</td>
                    <td className="text-right py-2">
                      {stat.daily_limit > 0 
                        ? ((stat.daily_used / stat.daily_limit) * 100).toFixed(1) 
                        : '0.0'}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default TokenBudgetChart