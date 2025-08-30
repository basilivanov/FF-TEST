import React, { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shadcn/ui/card'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { Badge } from '@/shadcn/ui/badge'
import { 
  GitBranch, 
  AlertTriangle, 
  Info, 
  Settings,
  Search
} from 'lucide-react'
import CallGraphVisualization from '@/components/CallGraphVisualization'

const CallGraph: React.FC = () => {
  console.log('[CallGraph Page] Component mounting...')
  const [maxNodes, setMaxNodes] = useState(50)
  const [moduleFilter, setModuleFilter] = useState('')

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <GitBranch className="h-8 w-8" />
            System Dependencies
          </h1>
          <p className="text-muted-foreground mt-2">
            Interactive visualization of module dependencies and call graph
          </p>
        </div>
      </div>

      {/* Mission Critical Info */}
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader className="pb-3">
          <CardTitle className="text-amber-800 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Mission Critical System Monitoring
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-blue-100 text-blue-800">API</Badge>
              <span>External interfaces & endpoints</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-red-100 text-red-800">LLM</Badge>
              <span>AI processing & routing</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-green-100 text-green-800">DB</Badge>
              <span>Data persistence & models</span>
            </div>
          </div>
          <div className="mt-4 p-3 bg-white rounded-lg border">
            <p className="text-xs text-muted-foreground">
              <Info className="h-4 w-4 inline mr-1" />
              Use this visualization to: identify bottlenecks, trace error propagation, 
              plan deployments, and analyze system impact before changes.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Visualization Controls
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-48">
              <label className="text-sm font-medium block mb-2">Module Filter</label>
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-muted-foreground" />
                <Input
                  placeholder="Filter by module name (e.g., api, llm, db)"
                  value={moduleFilter}
                  onChange={(e) => setModuleFilter(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="w-32">
              <label className="text-sm font-medium block mb-2">Max Nodes</label>
              <Input
                type="number"
                min={10}
                max={200}
                value={maxNodes}
                onChange={(e) => setMaxNodes(Number(e.target.value) || 50)}
              />
            </div>
            
            <Button 
              onClick={() => {
                setModuleFilter('')
                setMaxNodes(50)
              }}
              variant="outline"
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>System Dependencies Graph</CardTitle>
        </CardHeader>
        <CardContent>
          <CallGraphVisualization maxNodes={maxNodes} moduleFilter={moduleFilter} />
        </CardContent>
      </Card>

      {/* Usage Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>How to Use</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="font-medium mb-2">🎯 For Operations Team</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• Monitor critical paths in real-time</li>
                <li>• Identify cascading failure points</li>
                <li>• Plan maintenance windows</li>
                <li>• Track system health visually</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">🔧 For Development Team</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• Analyze code dependencies</li>
                <li>• Find architectural bottlenecks</li>
                <li>• Plan refactoring efforts</li>
                <li>• Understand module interactions</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">🚨 Crisis Response</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• Quickly assess impact scope</li>
                <li>• Trace error propagation paths</li>
                <li>• Prioritize recovery actions</li>
                <li>• Coordinate team responses</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">📊 Interaction Tips</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• Drag nodes to reorganize layout</li>
                <li>• Click nodes to see details</li>
                <li>• Use mouse wheel to zoom</li>
                <li>• Larger nodes = more connections</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CallGraph