import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button } from '@/shadcn/ui/button'
import { 
  LayoutDashboard, 
  Layers, 
  Play, 
  FileText, 
  Coins, 
  BookOpen, 
  Settings, 
  MessageCircle,
  Menu,
  X,
  AlertTriangle,
  Library,
  GitBranch,
  Bot
} from 'lucide-react'
import AlertBar from '@/components/AlertBar'

interface AppShellProps {
  children: React.ReactNode
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  // Close sidebar when route changes (for mobile)
  useEffect(() => {
    setSidebarOpen(false)
  }, [location])

  // Navigation items
  const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Agents', href: '/agents', icon: Bot },
    { name: 'Now', href: '/now', icon: Play },
    { name: 'Queue', href: '/queue', icon: Layers },
    { name: 'Errors', href: '/errors', icon: AlertTriangle },
    { name: 'Budget', href: '/budget', icon: Coins },
    { name: 'Features', href: '/features', icon: Library },
    { name: 'Tasks', href: '/tasks', icon: Library },
    { name: 'Runs', href: '/runs', icon: Play },
    { name: 'Logs', href: '/logs', icon: FileText },
    { name: 'Tokens', href: '/tokens', icon: Coins },
    { name: 'Граф', href: '/call-graph', icon: GitBranch },
    { name: 'Docs', href: '/docs', icon: BookOpen },
    { name: 'Settings', href: '/settings', icon: Settings },
    { name: 'Chat', href: '/chat', icon: MessageCircle },
  ]

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 flex flex-col ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <h1 className="text-xl font-bold text-gray-800 dark:text-white">Feature Factory</h1>
          <Button 
            variant="ghost" 
            size="icon" 
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        <nav className="flex-1 overflow-y-auto mt-6 px-2 pb-4">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-600 dark:bg-blue-900 dark:text-blue-300'
                        : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className="h-5 w-5 mr-3" />
                    <span>{item.name}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex flex-col flex-1 w-full overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <Button 
              variant="ghost" 
              size="icon" 
              className="mr-2 lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-6 w-6" />
            </Button>
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
              {navItems.find(item => item.href === location.pathname)?.name || 'Feature Factory'}
            </h2>
          </div>
          <div className="flex items-center space-x-4">
            {/* Environment badge */}
            <div className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full dark:bg-yellow-900 dark:text-yellow-100">
              TEST
            </div>
            {/* User menu placeholder */}
            <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600"></div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 md:p-6">
          {/* Global alerts */}
          <AlertBar />
          {children}
        </main>
      </div>
    </div>
  )
}
