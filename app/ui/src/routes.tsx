import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Dashboard from '@/pages/Dashboard'
import Features from '@/pages/Features'
import FeatureDetail from '@/pages/FeatureDetail'
import Tasks from '@/pages/Tasks'
import TaskDetail from '@/pages/TaskDetail'
import Runs from '@/pages/Runs'
import RunDetail from '@/pages/RunDetail'
import Logs from '@/pages/Logs'
import Errors from '@/pages/Errors'
import Tokens from '@/pages/Tokens'
import Docs from '@/pages/Docs'
import Settings from '@/pages/Settings'
import Chat from '@/pages/Chat'
import Now from '@/pages/Now'
import Queue from '@/pages/Queue'
import Budget from '@/pages/Budget'
import CallGraph from '@/pages/CallGraph'

export const routes = (
  <Routes>
    <Route path="/" element={<Dashboard />} />
    {/* Admin aliases for deep-links */}
    <Route path="/admin" element={<Dashboard />} />
    <Route path="/admin/features" element={<Features />} />
    <Route path="/admin/features/:id" element={<FeatureDetail />} />
    <Route path="/admin/runs" element={<Runs />} />
    <Route path="/admin/runs/:id" element={<RunDetail />} />
    <Route path="/admin/tasks/:id" element={<TaskDetail />} />
    <Route path="/admin/logs" element={<Logs />} />
    <Route path="/admin/errors" element={<Errors />} />
    <Route path="/admin/llm-metrics" element={<Tokens />} />
    <Route path="/admin/call-graph" element={<CallGraph />} />

    <Route path="/now" element={<Now />} />
    <Route path="/queue" element={<Queue />} />
    <Route path="/errors" element={<Errors />} />
    <Route path="/budget" element={<Budget />} />
    <Route path="/features" element={<Features />} />
    <Route path="/features/:id" element={<FeatureDetail />} />
    <Route path="/tasks" element={<Tasks />} />
    <Route path="/tasks/:id" element={<TaskDetail />} />
    <Route path="/runs" element={<Runs />} />
    <Route path="/runs/:id" element={<RunDetail />} />
    <Route path="/logs" element={<Logs />} />
    <Route path="/tokens" element={<Tokens />} />
    <Route path="/docs" element={<Docs />} />
    <Route path="/settings" element={<Settings />} />
    <Route path="/chat" element={<Chat />} />
    <Route path="/call-graph" element={<CallGraph />} />
  </Routes>
)
