export interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export type ThinkingStatus = 'pending' | 'running' | 'done' | 'error'

export interface ThinkingStep {
  key: string
  label: string
  status: ThinkingStatus
  startedAt?: number
  doneAt?: number
  detail?: string
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  sql_query?: string
  query_result?: string
  chart_config?: ChartConfig
  created_at: string
  thinkingSteps?: ThinkingStep[]
}

export interface ChartConfig {
  chartType: 'bar' | 'line' | 'pie' | 'scatter' | 'table'
  title?: string
  option: Record<string, unknown>
}

export interface SSEEvent {
  event: 'sql' | 'query_result' | 'answer' | 'chart' | 'error' | 'done'
  data: string
}
