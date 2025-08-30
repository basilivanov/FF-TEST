import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Badge } from '@/shadcn/ui/badge'
import { Button } from '@/shadcn/ui/button'
import { RefreshCw, Zap, Database, Globe, Settings, Users } from 'lucide-react'

interface Node {
  id: string
  name: string
  type: string
  color: string
  size: number
  incoming: number
  outgoing: number
  total_connections: number
  x?: number
  y?: number
}

interface Link {
  source: string | Node
  target: string | Node
  weight: number
  file_path: string
  full_source: string
  full_target: string
}

interface CallGraphData {
  nodes: Node[]
  links: Link[]
  stats: {
    total_nodes: number
    total_edges: number
    module_types: Record<string, number>
  }
  metadata: {
    generated_at: string
    max_nodes_requested: number
    module_filter: string | null
  }
}

interface CallGraphVisualizationProps {
  maxNodes?: number
  moduleFilter?: string
  height?: number
  width?: number
}

const MODULE_ICONS: Record<string, React.ComponentType> = {
  api: Globe,
  llm: Zap,
  database: Database,
  admin: Settings,
  graph: Users,
  utils: Settings
}

const CallGraphVisualization: React.FC<CallGraphVisualizationProps> = ({
  maxNodes = 50,
  moduleFilter,
  height = 600,
  width = 800
}) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [data, setData] = useState<CallGraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  const fetchGraphData = async () => {
    try {
      console.log('[CallGraph] Starting fetch...')
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams({
        limit: (maxNodes * 6).toString(), // Увеличиваем лимит для получения Python файлов
        offset: '0',
        ...(moduleFilter && { module_filter: moduleFilter })
      })
      
      // Правильный путь к API (бэкенд индексатора)
      const url = `/api/v1/index/calls?${params}`
      console.log('[CallGraph] Fetching URL:', url)
      
      const response = await fetch(url, {
        headers: {
          'X-Correlation-Id': `ui-call-graph-${Date.now()}`,
          'Content-Type': 'application/json'
        }
      })
      
      console.log('[CallGraph] Response status:', response.status)
      console.log('[CallGraph] Response headers:', Object.fromEntries(response.headers.entries()))
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('[CallGraph] Response error:', errorText)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const payload = await response.json()
      // Адаптируем ответ API /api/v1/index/calls (edges[]) к внутренней модели
      const edges: any[] = payload.edges || []
      const nodeMap: Record<string, Node> = {}
      const links: Link[] = edges.map((e: any) => {
        const s = e.source_symbol || e.source || e.source_symbol_name
        const t = e.target_symbol || e.target || e.target_symbol_name
        
        // Определяем тип и цвет узла
        const getNodeProps = (symbol: string) => {
          if (symbol.includes('.py')) return { type: 'api', color: '#ef4444' } // Python - красный
          if (symbol.includes('api')) return { type: 'api', color: '#3b82f6' } // API - синий  
          if (symbol.includes('llm')) return { type: 'llm', color: '#f59e0b' } // LLM - янтарный
          if (symbol.includes('db') || symbol.includes('database')) return { type: 'database', color: '#10b981' } // DB - зелёный
          if (symbol.includes('admin')) return { type: 'admin', color: '#8b5cf6' } // Admin - фиолетовый
          return { type: 'module', color: '#6b7280' } // Default - серый
        }
        
        if (s && !nodeMap[s]) {
          const props = getNodeProps(s)
          nodeMap[s] = { id: s, name: s, ...props, size: 14, incoming: 0, outgoing: 0, total_connections: 0 }
        }
        if (t && !nodeMap[t]) {
          const props = getNodeProps(t)
          nodeMap[t] = { id: t, name: t, ...props, size: 14, incoming: 0, outgoing: 0, total_connections: 0 }
        }
        if (s && nodeMap[s]) { nodeMap[s].outgoing += 1; nodeMap[s].total_connections += 1 }
        if (t && nodeMap[t]) { nodeMap[t].incoming += 1; nodeMap[t].total_connections += 1 }
        return {
          source: s,
          target: t,
          weight: Math.max(1, (e.weight || 1)),
          file_path: e.file_path || 'N/A',
          full_source: s,
          full_target: t,
        }
      }).slice(0, maxNodes * 6) // Увеличиваем лимит links
      
      // Сортируем nodes: сначала Python файлы, потом остальные
      const allNodes = Object.values(nodeMap)
      const pyNodes = allNodes.filter(n => n.id.includes('.py'))
      const otherNodes = allNodes.filter(n => !n.id.includes('.py'))
      const nodes: Node[] = [...pyNodes, ...otherNodes].slice(0, maxNodes)
      console.log('[CallGraph] Adapted data:', { nodes: nodes.length, links: links.length })
      setData({
        nodes,
        links,
        stats: { total_nodes: nodes.length, total_edges: links.length, module_types: { module: nodes.length } },
        metadata: { generated_at: new Date().toISOString(), max_nodes_requested: maxNodes, module_filter: moduleFilter || null }
      })
    } catch (err) {
      console.error('[CallGraph] Fetch error:', err)
      setError(err instanceof Error ? err.message : 'Failed to load graph data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Пытаемся загрузить реальные данные графа; при ошибке можно добавить мок
    fetchGraphData().catch(() => {
      // fallback-мок, если API временно недоступно
      setData({
        nodes: [
          { id: 'api', name: 'API Router', type: 'api', color: '#3b82f6', size: 20, incoming: 5, outgoing: 12, total_connections: 17 },
          { id: 'orchestrator', name: 'Orchestrator', type: 'core', color: '#ef4444', size: 25, incoming: 8, outgoing: 15, total_connections: 23 },
          { id: 'database', name: 'Database', type: 'db', color: '#10b981', size: 18, incoming: 15, outgoing: 3, total_connections: 18 },
          { id: 'llm_router', name: 'LLM Router', type: 'llm', color: '#f59e0b', size: 22, incoming: 6, outgoing: 8, total_connections: 14 },
          { id: 'auth', name: 'Auth Service', type: 'security', color: '#8b5cf6', size: 15, incoming: 3, outgoing: 5, total_connections: 8 }
        ],
        links: [
          { source: 'api', target: 'orchestrator', weight: 5, file_path: '/app/api/routes.py', full_source: 'API Router', full_target: 'Orchestrator' },
          { source: 'orchestrator', target: 'database', weight: 8, file_path: '/app/orchestrator/models.py', full_source: 'Orchestrator', full_target: 'Database' },
          { source: 'orchestrator', target: 'llm_router', weight: 3, file_path: '/app/orchestrator/agents.py', full_source: 'Orchestrator', full_target: 'LLM Router' },
          { source: 'api', target: 'auth', weight: 2, file_path: '/app/api/auth.py', full_source: 'API Router', full_target: 'Auth Service' }
        ],
        stats: { total_nodes: 5, total_edges: 4, module_types: { api: 1, core: 1, db: 1, llm: 1, security: 1 } },
        metadata: { generated_at: new Date().toISOString(), max_nodes_requested: maxNodes || 50, module_filter: moduleFilter || null }
      })
      setLoading(false)
    })
  }, [maxNodes, moduleFilter])

  useEffect(() => {
    console.log('[CallGraph] D3 useEffect triggered, data:', data?.nodes?.length || 0, 'nodes, svgRef:', !!svgRef.current)
    if (!data || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const { nodes, links } = data

    if (nodes.length === 0) return

    // Set up simulation
    const simulation = d3.forceSimulation(nodes as any)
      .force("link", d3.forceLink(links)
        .id((d: any) => d.id)
        .distance(80)
        .strength(0.3))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius((d: any) => d.size / 2 + 5))

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform)
      })

    svg.call(zoom)

    const container = svg.append('g')

    // Add links
    const link = container.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#94A3B8')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: any) => Math.min(d.weight / 5, 8))
      .attr('marker-end', 'url(#arrowhead)')

    // Add arrow markers
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('xoverflow', 'visible')
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10,0 L 0,5')
      .attr('fill', '#94A3B8')
      .style('stroke', 'none')

    // Add nodes
    const node = container.append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', (d: any) => d.size / 2)
      .attr('fill', (d: any) => d.color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag<SVGCircleElement, Node>()
        .on('start', (event, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d: any) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d: any) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        })
      )
      .on('click', (event, d) => {
        setSelectedNode(d)
      })
      .on('mouseover', function(event, d) {
        d3.select(this)
          .transition()
          .duration(100)
          .attr('r', (d.size / 2) * 1.2)
          .attr('stroke-width', 3)
      })
      .on('mouseout', function(event, d) {
        d3.select(this)
          .transition()
          .duration(100)
          .attr('r', d.size / 2)
          .attr('stroke-width', 2)
      })

    // Add labels
    const labels = container.append('g')
      .attr('class', 'labels')
      .selectAll('text')
      .data(nodes)
      .enter()
      .append('text')
      .text((d: any) => d.name.split('.').pop() || d.name)
      .attr('font-size', '10px')
      .attr('font-family', 'Arial, sans-serif')
      .attr('fill', '#1F2937')
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .style('pointer-events', 'none')

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y)

      labels
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y)
    })

    return () => {
      simulation.stop()
    }
  }, [data, width, height])

  const getTypeIcon = (type: string) => {
    const IconComponent = MODULE_ICONS[type] || Settings
    return <IconComponent className="h-4 w-4" />
  }

  if (loading) {
    console.log('[CallGraph] Rendering loading state')
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 animate-spin" />
            Loading Call Graph...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <p className="text-muted-foreground">Building dependency graph...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    console.log('[CallGraph] Rendering error state:', error)
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Call Graph</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-500 mb-4">{error}</p>
          <Button onClick={fetchGraphData} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    console.log('[CallGraph] No data, returning null')
    return null
  }

  console.log('[CallGraph] Rendering main component with data:', data.stats)

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Total Modules</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.stats.total_nodes}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Dependencies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.stats.total_edges}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Module Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-1">
              {Object.entries(data.stats.module_types).map(([type, count]) => (
                <Badge key={type} variant="outline" className="text-xs">
                  {getTypeIcon(type)}
                  <span className="ml-1">{type}: {count}</span>
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <Button onClick={fetchGraphData} size="sm" variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Main Graph */}
      <Card>
        <CardHeader>
          <CardTitle>System Dependencies Map</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <svg
                ref={svgRef}
                width={width}
                height={height}
                className="border rounded-lg"
              />
            </div>
            
            {/* Node Detail Panel */}
            {selectedNode && (
              <div className="w-80 space-y-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      {getTypeIcon(selectedNode.type)}
                      Selected Module
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="font-medium text-sm">{selectedNode.name}</p>
                      <Badge 
                        variant="outline" 
                        className="text-xs mt-1"
                        style={{ backgroundColor: selectedNode.color + '20', borderColor: selectedNode.color }}
                      >
                        {selectedNode.type}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="font-medium">Incoming</p>
                        <p className="text-muted-foreground">{selectedNode.incoming}</p>
                      </div>
                      <div>
                        <p className="font-medium">Outgoing</p>
                        <p className="text-muted-foreground">{selectedNode.outgoing}</p>
                      </div>
                    </div>
                    
                    <div>
                      <p className="font-medium text-sm">Total Connections</p>
                      <p className="text-2xl font-bold" style={{ color: selectedNode.color }}>
                        {selectedNode.total_connections}
                      </p>
                    </div>
                    
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => setSelectedNode(null)}
                    >
                      Close
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
          
          <div className="mt-4 text-xs text-muted-foreground">
            <p>• Node size = number of connections • Click nodes for details • Drag to reposition</p>
            <p>• Colors: API (blue), LLM (red), Database (green), Admin (purple), Graph (amber), Utils (gray)</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CallGraphVisualization
