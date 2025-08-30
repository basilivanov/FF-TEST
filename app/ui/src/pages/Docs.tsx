import React, { useState } from 'react'
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
  Filter
} from 'lucide-react'
import { formatDate } from '@/lib/format'
import { DocRegistryEntry } from '@/lib/types'

const Docs: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  
  // Mock data for documents
  const mockDocs: DocRegistryEntry[] = [
    {
      doc_name: 'Architecture.md',
      version: 'v1.1',
      content_hash: 'a1b2c3d4e5f6',
      updated_at: '2023-08-21T10:00:00Z'
    },
    {
      doc_name: 'API-Orchestrator-001.md',
      version: 'v1.0',
      content_hash: 'f6e5d4c3b2a1',
      updated_at: '2023-08-20T15:30:00Z'
    },
    {
      doc_name: 'ChangePolicy-000.md',
      version: 'v1.2',
      content_hash: '1a2b3c4d5e6f',
      updated_at: '2023-08-19T09:15:00Z'
    },
    {
      doc_name: 'Logging-001.md',
      version: 'v1.1',
      content_hash: '6f5e4d3c2b1a',
      updated_at: '2023-08-18T14:20:00Z'
    },
    {
      doc_name: 'Policy-LLM-000.md',
      version: 'v1.3',
      content_hash: 'b2c3d4e5f6a1',
      updated_at: '2023-08-17T11:45:00Z'
    },
    {
      doc_name: 'Schema-000-base-tables.md',
      version: 'v1.0',
      content_hash: 'c3d4e5f6a1b2',
      updated_at: '2023-08-16T16:30:00Z'
    },
    {
      doc_name: 'Security-000.md',
      version: 'v1.0',
      content_hash: 'd4e5f6a1b2c3',
      updated_at: '2023-08-15T13:20:00Z'
    },
    {
      doc_name: 'UI-000.md',
      version: 'v1.0',
      content_hash: 'e5f6a1b2c3d4',
      updated_at: '2023-08-21T11:00:00Z'
    }
  ]

  // Status options for filtering
  const statusOptions = ['Up to date', 'Outdated', 'Draft']

  // Filter documents based on search term and status filter
  const filteredDocs = mockDocs.filter(doc => {
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
    // In a real implementation, this would open the document in a viewer
    console.log(`Viewing document: ${docName}`)
  }

  // Download document
  const downloadDocument = (docName: string) => {
    // In a real implementation, this would download the document
    console.log(`Downloading document: ${docName}`)
  }

  // Rebuild documentation
  const rebuildDocumentation = () => {
    // In a real implementation, this would trigger a documentation rebuild
    console.log('Rebuilding documentation...')
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Docs</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Управление документацией и ее актуальность
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <Button onClick={rebuildDocumentation}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Пересобрать документацию
          </Button>
        </div>
      </div>

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

      {/* Summary */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Сводка документации</h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Всего документов: {mockDocs.length}
            </p>
          </div>
          <div className="mt-4 md:mt-0 flex space-x-4">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Актуальные</p>
              <p className="text-2xl font-semibold text-green-600 dark:text-green-400">
                {mockDocs.filter(d => d.doc_name !== 'UI-000.md').length}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Устаревшие</p>
              <p className="text-2xl font-semibold text-yellow-600 dark:text-yellow-400">0</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Черновики</p>
              <p className="text-2xl font-semibold text-blue-600 dark:text-blue-400">1</p>
            </div>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Название документа
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Версия
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Хэш содержимого
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Обновлено
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Статус
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
                      <BookOpen className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {doc.doc_name}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    {doc.version}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500 dark:text-gray-400">
                    {doc.content_hash}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1" />
                      {formatDate(doc.updated_at)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {doc.doc_name === 'UI-000.md' ? (
                      <Badge variant="secondary">Черновик</Badge>
                    ) : (
                      <Badge variant="default">Актуальный</Badge>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => viewDocument(doc.doc_name)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadDocument(doc.doc_name)}
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
      </div>

      {/* Empty state */}
      {filteredDocs.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Документы не найдены</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Попробуйте изменить параметры поиска или фильтрации.
          </p>
        </div>
      )}
    </div>
  )
}

export default Docs
