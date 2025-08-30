import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { 
  Coins, 
  RefreshCw
} from 'lucide-react'
import { get } from '@/lib/api'
import TokenBudgetChart from '@/components/TokenBudgetChart'

interface TokenUsage {
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

const Budget: React.FC = () => {
  const [tokenUsages, setTokenUsages] = useState<TokenUsage[]>([])
  const [budgetSummary, setBudgetSummary] = useState<BudgetSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Мок данные для быстрой загрузки
        setTokenUsages([
          { role: 'coder', model: 'claude-3', input_tokens: 25000, output_tokens: 15000, total_tokens: 40000, cost: 12.50, daily_limit: 100000, daily_used: 40000, daily_remaining: 60000 },
          { role: 'architect', model: 'gpt-4', input_tokens: 8000, output_tokens: 12000, total_tokens: 20000, cost: 8.75, daily_limit: 50000, daily_used: 20000, daily_remaining: 30000 },
          { role: 'reviewer', model: 'gemini-pro', input_tokens: 15000, output_tokens: 8000, total_tokens: 23000, cost: 5.20, daily_limit: 75000, daily_used: 23000, daily_remaining: 52000 }
        ])
        setBudgetSummary({
          total_daily_limit: 225000,
          total_daily_used: 83000,
          total_daily_remaining: 142000,
          roles_summary: {
            coder: { daily_limit: 100000, daily_used: 40000, daily_remaining: 60000, percentage_used: 40 },
            architect: { daily_limit: 50000, daily_used: 20000, daily_remaining: 30000, percentage_used: 40 },
            reviewer: { daily_limit: 75000, daily_used: 23000, daily_remaining: 52000, percentage_used: 30.7 }
          }
        })
        setError(null)
      } catch (err) {
        console.error('Budget: unexpected error', err)
        setError('Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Ошибка! </strong>
        <span className="block sm:inline">{error}</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Budget</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Статистика использования токенов и бюджетов по ролям и моделям
        </p>
      </div>

      {budgetSummary && (
        <TokenBudgetChart 
          tokenStats={tokenUsages} 
          budgetSummary={budgetSummary} 
        />
      )}

      {/* Action Buttons */}
      <div className="flex justify-end">
        <button 
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          onClick={() => window.location.reload()}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Обновить
        </button>
      </div>
    </div>
  )
}

export default Budget
