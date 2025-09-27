import React, { useEffect, useMemo, useState } from 'react'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { Badge } from '@/shadcn/ui/badge'
import { Search, BarChart3, RefreshCw, Filter } from 'lucide-react'
import { formatRole } from '@/lib/format'
import { get } from '@/lib/api'

const Tokens: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState<string | null>(null)

  type RoleStats = { daily_limit: number; used_tokens: number; remaining_tokens: number; usage_percentage: number; calls_count: number; last_call?: string | null }
  const [statsByRole, setStatsByRole] = useState<Record<string, RoleStats>>({})
  const [totalLimit, setTotalLimit] = useState(0)
  const [totalUsed, setTotalUsed] = useState(0)
  const [totalRemaining, setTotalRemaining] = useState(0)
  const [overallPct, setOverallPct] = useState(0)

  const fetchData = async () => {
    try {
      setLoading(true)
      const auth = 'Basic ' + btoa('ops:ops123')
      const resp = await get<any>('/admin/tokens', { headers: { Authorization: auth } })
      const data = resp.data
      const sb: Record<string, RoleStats> = data?.stats_by_role || {}
      setStatsByRole(sb)
      setTotalLimit(data?.total_usage?.total_limit || 0)
      setTotalUsed(data?.total_usage?.total_used || 0)
      setTotalRemaining(data?.total_usage?.total_remaining || 0)
      setOverallPct(data?.total_usage?.overall_percentage || 0)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить статистику токенов')
      setStatsByRole({})
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const roles = useMemo(() => Object.keys(statsByRole).sort(), [statsByRole])
  const filteredRoles = roles.filter(r => {
    const term = searchTerm.trim().toLowerCase()
    if (term && !r.toLowerCase().includes(term)) return false
    if (roleFilter && r !== roleFilter) return false
    return true
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Tokens</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Сводка расхода токенов по ролям</p>
        </div>
        <div className="mt-4 md:mt-0">
          <Button onClick={fetchData} disabled={loading}>
            <RefreshCw className="mr-2 h-4 w-4" />
            {loading ? 'Обновляем…' : 'Обновить данные'}
          </Button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-4 md:space-y-0">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Поиск по роли..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">Роль:</span>
            <Badge variant={!roleFilter ? 'default' : 'outline'} className="cursor-pointer" onClick={() => setRoleFilter(null)}>Все</Badge>
            {roles.map(role => (
              <Badge key={role} variant={roleFilter === role ? 'default' : 'outline'} className="cursor-pointer" onClick={() => setRoleFilter(role)}>
                {formatRole(role)}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Всего лимит</h3>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{totalLimit.toLocaleString()}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Использовано</h3>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{totalUsed.toLocaleString()} ({Math.round(overallPct)}%)</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Остаток</h3>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{totalRemaining.toLocaleString()}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-yellow-500" />
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Ролей с риском</h3>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{roles.filter(r => (statsByRole[r]?.usage_percentage || 0) > 80).length}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Роль</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Использовано / Лимит</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Остаток</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Вызовов</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Последний вызов</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-900 dark:divide-gray-700">
              {filteredRoles.map((role) => {
                const s = statsByRole[role]
                return (
                  <tr key={role} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-6 py-4 whitespace-nowrap"><div className="text-sm font-medium text-gray-900 dark:text-white">{formatRole(role)}</div></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{(s?.used_tokens || 0).toLocaleString()} / {(s?.daily_limit || 0).toLocaleString()} ({Math.round(s?.usage_percentage || 0)}%)</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{(s?.remaining_tokens || 0).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{s?.calls_count || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{s?.last_call ? new Date(s.last_call).toLocaleString() : '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{error}</div>
      )}
    </div>
  )
}

export default Tokens

