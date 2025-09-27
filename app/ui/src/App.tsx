import React, { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/AppShell'
import ErrorBoundary from '@/components/ErrorBoundary'
import { installGlobalClientErrorHooks } from '@/lib/clientLog'
import Dashboard from '@/pages/Dashboard'
import Features from '@/pages/Features'
import FeatureDetail from '@/pages/FeatureDetail'
import Tasks from '@/pages/Tasks'
import Runs from '@/pages/Runs'
import RunDetail from '@/pages/RunDetail'
import TaskDetail from '@/pages/TaskDetail'
import Logs from '@/pages/Logs'
import Tokens from '@/pages/Tokens'
import Docs from '@/pages/Docs'
import Settings from '@/pages/Settings'
import Chat from '@/pages/Chat'
import Now from '@/pages/Now'
import Queue from '@/pages/Queue'
import Errors from '@/pages/Errors'
import Budget from '@/pages/Budget'
import Agents from '@/pages/Agents'
import CallGraph from '@/pages/CallGraph'

const App: React.FC = () => {
  useEffect(() => { installGlobalClientErrorHooks() }, [])
  return (
    <ErrorBoundary>
      <AppShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="agents" element={<Agents />} />
        <Route path="now" element={<Now />} />
        <Route path="queue" element={<Queue />} />
        <Route path="errors" element={<Errors />} />
        <Route path="budget" element={<Budget />} />
        <Route path="features" element={<Features />} />
        <Route path="features/:id" element={<FeatureDetail />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="tasks/:id" element={<TaskDetail />} />
        <Route path="runs" element={<Runs />} />
        <Route path="runs/:id" element={<RunDetail />} />
        <Route path="logs" element={<Logs />} />
        <Route path="tokens" element={<Tokens />} />
        <Route path="call-graph" element={<CallGraph />} />
        <Route path="docs" element={<Docs />} />
        <Route path="settings" element={<Settings />} />
        <Route path="chat" element={<Chat />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </AppShell>
    </ErrorBoundary>
  )
}

export default App
