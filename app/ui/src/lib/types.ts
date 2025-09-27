export interface DocRegistryEntry {
  doc_name: string
  version: string
  content_hash: string
  updated_at: string
}

export type LogSeverity = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL'

export interface LogEntry {
  timestamp: string
  level: LogSeverity
  service: string
  message: string
  correlation_id: string | null
  request_id?: string | null
  user?: string | null
  source: string
  feature_id?: number | null
  task_id?: number | null
  run_id?: string | null
  duration_ms?: number | null
  status_code?: number | null
  ip_address?: string | null
  user_agent?: string | null
  error?: any
  context?: Record<string, any> | null
}

export type Role = 'Dev' | 'Architect' | 'QA' | 'Scribe' | 'Apply' | 'Maintainer' | 'Gate'

export interface TokenUsage {
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

