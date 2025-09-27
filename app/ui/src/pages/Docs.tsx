import React, { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { Badge } from '@/shadcn/ui/badge'
import {
  Search,
  Calendar,
  BookOpen,
  RefreshCw,
  Download,
  Eye,
  Filter,
  Brain,
  Users,
  Code,
  TestTube,
  Wrench,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Database,
  Zap,
  Heart,
  BarChart3,
  Activity,
  Shield,
  FileText,
  Globe
} from 'lucide-react'
import { formatDate } from '@/lib/format'
import { DocRegistryEntry } from '@/lib/types'
import { get, post } from '@/lib/api'
import { Sparkline } from '@/components/Sparkline'
import { ProgressRing } from '@/components/ProgressRing'

// Helper function to get role icon
const getRoleIcon = (roleName: string) => {
  switch (roleName.toLowerCase()) {
    case 'architect':
      return Users
    case 'dev':
    case 'developer':
      return Code
    case 'qa':
      return TestTube
    case 'scribe':
      return BookOpen
    case 'maintainer':
      return Wrench
    default:
      return FileText
  }
}

interface CortexHealth {
  overall_score: number
  context_freshness: number
  role_coverage: number
  knowledge_completeness: number
  last_updated: string
}

interface RoleAnalysis {
  role: string
  context_quality: number
  last_updated: string
  docs_count: number
  issues: string[]
  icon: React.ComponentType<any>
}

interface KnowledgeBase {
  total_docs: number
  active_docs: number
  outdated_docs: number
  broken_links: number
  coverage_percentage: number
  last_audit: string
}

const Docs: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [docs, setDocs] = useState<DocRegistryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cortexHealth, setCortexHealth] = useState<CortexHealth | null>(null)
  const [roleAnalysis, setRoleAnalysis] = useState<RoleAnalysis[]>([])
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null)
  const [tab, setTab] = useState<'health' | 'docs' | 'analysis'>('health')

  const loadData = async () => {
    try {
      setLoading(true)

      // Load docs registry
      const docsResp = await get<{ docs: DocRegistryEntry[] }>(`/docs/status`)
      setDocs(docsResp.data?.docs || [])

      // Fetch real cortex health data
      const cortexResp = await get('/cortex/health')

      if (cortexResp.error) {
        console.error('Failed to fetch cortex health:', cortexResp.error)
        // Fallback to basic data
        const fallbackHealth: CortexHealth = {
          overall_score: 0,
          context_freshness: 0,
          role_coverage: 0,
          knowledge_completeness: 0,
          last_updated: new Date().toISOString()
        }
        setCortexHealth(fallbackHealth)
      } else {
        const realHealth: CortexHealth = {
          overall_score: cortexResp.data?.overall_score || 0,
          context_freshness: cortexResp.data?.context_freshness || 0,
          role_coverage: cortexResp.data?.role_coverage || 0,
          knowledge_completeness: cortexResp.data?.knowledge_completeness || 0,
          last_updated: cortexResp.data?.last_updated || new Date().toISOString()
        }
        setCortexHealth(realHealth)
      }

      // Process real role analysis data
      if (!cortexResp.error && cortexResp.data?.roles) {
        const realRoles: RoleAnalysis[] = cortexResp.data.roles.map((role: any) => ({
          role: role.role,
          context_quality: role.context_quality || 0,
          last_updated: role.last_updated || new Date().toISOString(),
          docs_count: role.docs_count || 0,
          issues: role.issues || [],
          icon: getRoleIcon(role.role)
        }))
        setRoleAnalysis(realRoles)
      } else {
        // Fallback to empty roles
        setRoleAnalysis([])
      }

      // Calculate knowledge base stats from real data
      const totalDocs = docsResp.data?.docs?.length || 0
      const roles = !cortexResp.error && cortexResp.data?.roles ? cortexResp.data.roles : []
      const realKB: KnowledgeBase = {
        total_docs: totalDocs,
        active_docs: roles.reduce((sum: number, role: any) => sum + (role.docs_count || 0), 0),
        outdated_docs: roles.filter((role: any) => (role.issues || []).length > 0).length,
        broken_links: roles.reduce((sum: number, role: any) =>
          sum + (role.issues || []).filter((issue: string) => issue.toLowerCase().includes('link')).length, 0),
        coverage_percentage: !cortexResp.error && cortexResp.data?.overall_score ? cortexResp.data.overall_score : 0,
        last_audit: !cortexResp.error && cortexResp.data?.last_updated ? cortexResp.data.last_updated : new Date().toISOString()
      }
      setKnowledgeBase(realKB)

      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить данные')
      setDocs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Status options for filtering
  const statusOptions = ['Up to date', 'Outdated', 'Draft']

  // Filter documents based on search term and status filter
  const filteredDocs = docs.filter(doc => {
    const matchesSearch = searchTerm === '' || 
      doc.doc_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.version.toLowerCase().includes(searchTerm.toLowerCase())
    
    // In a real implementation, we would check the actual status
    // For now, we'll assume all documents are up to date
    const matchesStatus = statusFilter === null || statusFilter === 'Up to date'
    
    return matchesSearch && matchesStatus
  })

  // Toggle status filter
  const toggleStatusFilter = (status: string | null) => {
    setStatusFilter(status)
  }

  // View document
  const viewDocument = (docName: string) => {
    window.open(`/cortex/docs/${docName}`, '_blank')
  }

  const downloadDocument = (docName: string) => {
    window.open(`/cortex/docs/${docName}`, '_blank')
  }

  // Rebuild documentation
  const [rebuilding, setRebuilding] = useState(false)
  const rebuildDocumentation = async () => {
    try {
      setRebuilding(true)
      await post(`/docs/rebuild`)
      const resp = await get<{ docs: DocRegistryEntry[] }>(`/docs/status`)
      setDocs(resp.data?.docs || [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось пересобрать документацию')
    } finally {
      setRebuilding(false)
    }
  }

  // Trigger cortex analysis
  const [analyzing, setAnalyzing] = useState(false)
  const triggerCortexAnalysis = async () => {
    try {
      setAnalyzing(true)
      await post('/cortex/analyze')
      // Reload data after a short delay to give analysis time to complete
      setTimeout(loadData, 2000)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось запустить анализ кортекса')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <Brain className="h-8 w-8 mr-3 text-blue-600" />
            Cortex Health & Documentation
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Мониторинг здоровья кортекса, качества контекста и базы знаний
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center space-x-2">
          <Button onClick={triggerCortexAnalysis} disabled={analyzing} variant="outline">
            <Brain className={`mr-2 h-4 w-4 ${analyzing ? 'animate-spin' : ''}`} />
            {analyzing ? 'Анализируем…' : 'Анализ кортекса'}
          </Button>
          <Button onClick={rebuildDocumentation} disabled={rebuilding} variant="outline">
            <RefreshCw className={`mr-2 h-4 w-4 ${rebuilding ? 'animate-spin' : ''}`} />
            {rebuilding ? 'Пересобираем…' : 'Пересобрать'}
          </Button>
          {cortexHealth && (
            <Badge variant={cortexHealth.overall_score >= 85 ? 'default' : cortexHealth.overall_score >= 70 ? 'secondary' : 'destructive'}>
              <Heart className="h-3 w-3 mr-1" />
              Здоровье: {cortexHealth.overall_score}%
            </Badge>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-2 border-b pb-2 overflow-x-auto">
        <Button
          size="sm"
          variant={tab === 'health' ? 'default' : 'outline'}
          onClick={() => setTab('health')}
        >
          <Heart className="h-4 w-4 mr-2" />
          Здоровье Кортекса
        </Button>
        <Button
          size="sm"
          variant={tab === 'analysis' ? 'default' : 'outline'}
          onClick={() => setTab('analysis')}
        >
          <BarChart3 className="h-4 w-4 mr-2" />
          Анализ Ролей
        </Button>
        <Button
          size="sm"
          variant={tab === 'docs' ? 'default' : 'outline'}
          onClick={() => setTab('docs')}
        >
          <BookOpen className="h-4 w-4 mr-2" />
          Документация
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{error}</div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      )}

      {/* Health Tab */}
      {tab === 'health' && cortexHealth && knowledgeBase && !loading && (
        <div className="space-y-6">
          {/* Overall Health Score */}
          <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Heart className="h-5 w-5 mr-2" />
                Общее состояние Кортекса
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center">
                <ProgressRing
                  value={cortexHealth.overall_score}
                  max={100}
                  size={120}
                  strokeWidth={8}
                  gradientFrom={cortexHealth.overall_score >= 85 ? "#10B981" : cortexHealth.overall_score >= 70 ? "#F59E0B" : "#EF4444"}
                  gradientTo={cortexHealth.overall_score >= 85 ? "#059669" : cortexHealth.overall_score >= 70 ? "#D97706" : "#DC2626"}
                />
                <div className="ml-8">
                  <div className="text-4xl font-bold text-blue-600">{cortexHealth.overall_score}%</div>
                  <div className="text-lg text-gray-600">здоровье системы</div>
                  <div className="text-sm text-gray-500 mt-2">
                    Последнее обновление: {formatDate(cortexHealth.last_updated)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Health Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4" />
                  <span>Свежесть контекста</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{cortexHealth.context_freshness}%</div>
                <div className="text-sm text-gray-600">актуальность информации</div>
                <Sparkline
                  data={[88, 92, 85, 90, 95, 91, 89, cortexHealth.context_freshness]}
                  width={120}
                  height={30}
                  color="#10B981"
                  animate={true}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <Shield className="h-4 w-4" />
                  <span>Покрытие ролей</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{cortexHealth.role_coverage}%</div>
                <div className="text-sm text-gray-600">готовность агентов</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${cortexHealth.role_coverage}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center space-x-2">
                  <Database className="h-4 w-4" />
                  <span>Полнота знаний</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">{cortexHealth.knowledge_completeness}%</div>
                <div className="text-sm text-gray-600">база знаний</div>
                <ProgressRing
                  value={cortexHealth.knowledge_completeness}
                  max={100}
                  size={40}
                  strokeWidth={3}
                  gradientFrom="#8B5CF6"
                  gradientTo="#7C3AED"
                />
              </CardContent>
            </Card>
          </div>

          {/* Knowledge Base Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="h-5 w-5 mr-2" />
                Состояние базы знаний
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">{knowledgeBase.total_docs}</div>
                  <div className="text-sm text-gray-600">всего документов</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{knowledgeBase.active_docs}</div>
                  <div className="text-sm text-gray-600">активные</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">{knowledgeBase.outdated_docs}</div>
                  <div className="text-sm text-gray-600">устаревшие</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{knowledgeBase.broken_links}</div>
                  <div className="text-sm text-gray-600">битые ссылки</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{knowledgeBase.coverage_percentage}%</div>
                  <div className="text-sm text-gray-600">покрытие</div>
                </div>
              </div>
              <div className="mt-4 text-sm text-gray-500">
                Последний аудит: {formatDate(knowledgeBase.last_audit)}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Role Analysis Tab */}
      {tab === 'analysis' && !loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {roleAnalysis.map((role) => {
            const Icon = role.icon
            return (
              <Card key={role.role}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Icon className="h-5 w-5 mr-2" />
                      {role.role}
                    </div>
                    <Badge variant={role.context_quality >= 85 ? 'default' : role.context_quality >= 70 ? 'secondary' : 'destructive'}>
                      {role.context_quality}%
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Качество контекста</span>
                        <span>{role.context_quality}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${
                            role.context_quality >= 85 ? 'bg-green-500' :
                            role.context_quality >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${role.context_quality}%` }}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Документов:</span>
                        <div className="font-medium">{role.docs_count}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Обновлено:</span>
                        <div className="font-medium">{formatDate(role.last_updated)}</div>
                      </div>
                    </div>

                    {role.issues.length > 0 && (
                      <div>
                        <div className="text-sm font-medium text-red-600 mb-2 flex items-center">
                          <AlertTriangle className="h-4 w-4 mr-1" />
                          Проблемы
                        </div>
                        <ul className="space-y-1">
                          {role.issues.map((issue, index) => (
                            <li key={index} className="text-sm text-red-600 pl-4">
                              • {issue}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {role.issues.length === 0 && (
                      <div className="flex items-center text-sm text-green-600">
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Проблем не обнаружено
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Documentation Tab */}
      {tab === 'docs' && !loading && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-4 md:space-y-0">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Поиск по названию документа или версии..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <div className="flex flex-wrap gap-2">
                <span className="text-sm text-gray-500 dark:text-gray-400">Статус:</span>
                <Badge
                  variant={!statusFilter ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => toggleStatusFilter(null)}
                >
                  Все
                </Badge>
                {statusOptions.map(status => (
                  <Badge
                    key={status}
                    variant={statusFilter === status ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => toggleStatusFilter(status)}
                  >
                    {status}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Documents Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BookOpen className="h-5 w-5 mr-2" />
                Реестр документации ({filteredDocs.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {filteredDocs.length === 0 ? (
                <div className="text-center py-12">
                  <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Документы не найдены</h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Попробуйте изменить параметры поиска или фильтрации.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Документ
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Версия
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Статус
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Обновлено
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Действия
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-900 dark:divide-gray-700">
                      {filteredDocs.map((doc, index) => (
                        <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <FileText className="h-5 w-5 text-gray-400 mr-3" />
                              <div>
                                <div className="text-sm font-medium text-gray-900 dark:text-white">
                                  {doc.doc_name}
                                </div>
                                <div className="text-xs text-gray-500 font-mono">
                                  {doc.content_hash}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                            {doc.version}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {doc.doc_name === 'UI-000.md' ? (
                              <Badge variant="secondary">Черновик</Badge>
                            ) : (
                              <Badge variant="default">Актуальный</Badge>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            <div className="flex items-center">
                              <Calendar className="h-4 w-4 mr-1" />
                              {formatDate(doc.updated_at)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => viewDocument(doc.doc_name)}
                                title="Просмотр"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => downloadDocument(doc.doc_name)}
                                title="Скачать"
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default Docs
