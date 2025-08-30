import React, { useState } from 'react'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { Badge } from '@/shadcn/ui/badge'
import { 
  Search, 
  Calendar,
  BarChart3,
  RefreshCw,
  Filter
} from 'lucide-react'
import { formatRole, formatDate } from '@/lib/format'
import { TokenUsage } from '@/lib/types'

const Tokens: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState<string | null>(null)
  const [modelFilter, setModelFilter] = useState<string | null>(null)
  
  // Mock data for token usage
  const mockTokenUsage: TokenUsage[] = [
    {
      role: 'Architect',
      model: 'claude-3-opus',
      input_tokens: 15000,
      output_tokens: 8000,
      total_tokens: 23000,
      cost: 0.46
    },
    {
      role: 'Dev',
      model: 'qwen-plus',
      input_tokens: 25000,
      output_tokens: 12000,
      total_tokens: 37000,
      cost: 0.37
    },
    {
      role: 'QA',
      model: 'gpt-4',
      input_tokens: 18000,
      output_tokens: 9000,
      total_tokens: 27000,
      cost: 0.54
    },
    {
      role: 'Scribe',
      model: 'gemini-pro',
      input_tokens: 12000,
      output_tokens: 6000,
      total_tokens: 18000,
      cost: 0.18
    },
    {
      role: 'Maintainer',
      model: 'claude-3-sonnet',
      input_tokens: 20000,
      output_tokens: 10000,
      total_tokens: 30000,
      cost: 0.30
    }
  ]

  // Role options for filtering
  const roleOptions = ['Architect', 'Dev', 'QA', 'Scribe', 'Maintainer']

  // Model options for filtering
  const modelOptions = ['claude-3-opus', 'claude-3-sonnet', 'qwen-plus', 'gpt-4', 'gemini-pro']

  // Filter token usage based on search term, role filter, and model filter
  const filteredTokenUsage = mockTokenUsage.filter(usage => {
    const matchesSearch = searchTerm === '' || 
      usage.role.toLowerCase().includes(searchTerm.toLowerCase()) ||
      usage.model.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesRole = roleFilter === null || usage.role === roleFilter
    
    const matchesModel = modelFilter === null || usage.model === modelFilter
    
    return matchesSearch && matchesRole && matchesModel
  })

  // Calculate totals
  const totals = filteredTokenUsage.reduce((acc, usage) => {
    acc.input_tokens += usage.input_tokens
    acc.output_tokens += usage.output_tokens
    acc.total_tokens += usage.total_tokens
    acc.cost += usage.cost
    return acc
  }, { input_tokens: 0, output_tokens: 0, total_tokens: 0, cost: 0 })

  // Toggle role filter
  const toggleRoleFilter = (role: string | null) => {
    setRoleFilter(role)
  }

  // Toggle model filter
  const toggleModelFilter = (model: string | null) => {
    setModelFilter(model)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Tokens</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Сводка расхода токенов по ролям и моделям
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <Button>
            <RefreshCw className="mr-2 h-4 w-4" />
            Обновить данные
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-4 md:space-y-0">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Поиск по роли или модели..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">Роль:</span>
            <Badge
              variant={!roleFilter ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => toggleRoleFilter(null)}
            >
              Все
            </Badge>
            {roleOptions.map(role => (
              <Badge
                key={role}
                variant={roleFilter === role ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleRoleFilter(role)}
              >
                {formatRole(role)}
              </Badge>
            ))}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">Модель:</span>
            <Badge
              variant={!modelFilter ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => toggleModelFilter(null)}
            >
              Все
            </Badge>
            {modelOptions.map(model => (
              <Badge
                key={model}
                variant={modelFilter === model ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleModelFilter(model)}
              >
                {model}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Входные токены</h3>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {totals.input_tokens.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Выходные токены</h3>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {totals.output_tokens.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-purple-500" />
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Всего токенов</h3>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {totals.total_tokens.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-yellow-500" />
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Стоимость ($)</h3>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {totals.cost.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Token Usage Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Роль
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Модель
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Входные токены
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Выходные токены
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Всего токенов
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Стоимость ($)
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-900 dark:divide-gray-700">
              {filteredTokenUsage.map((usage, index) => (
                <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {formatRole(usage.role)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {usage.model}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {usage.input_tokens.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {usage.output_tokens.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {usage.total_tokens.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    ${usage.cost.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <td className="px-6 py-3 text-sm font-medium text-gray-900 dark:text-white">
                  Итого
                </td>
                <td className="px-6 py-3"></td>
                <td className="px-6 py-3 text-sm font-medium text-gray-900 dark:text-white">
                  {totals.input_tokens.toLocaleString()}
                </td>
                <td className="px-6 py-3 text-sm font-medium text-gray-900 dark:text-white">
                  {totals.output_tokens.toLocaleString()}
                </td>
                <td className="px-6 py-3 text-sm font-medium text-gray-900 dark:text-white">
                  {totals.total_tokens.toLocaleString()}
                </td>
                <td className="px-6 py-3 text-sm font-medium text-gray-900 dark:text-white">
                  ${totals.cost.toFixed(2)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Empty state */}
      {filteredTokenUsage.length === 0 && (
        <div className="text-center py-12">
          <Coins className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Данные не найдены</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Попробуйте изменить параметры поиска или фильтрации.
          </p>
        </div>
      )}
    </div>
  )
}

export default Tokens
