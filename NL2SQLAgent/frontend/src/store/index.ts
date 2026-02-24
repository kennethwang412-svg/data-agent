import { create } from 'zustand'
import type { Session, Message, ChartConfig, ThinkingStep } from '../types'
import {
  fetchSessions,
  createSession as createSessionApi,
  fetchSessionDetail,
  deleteSessionApi,
  sendChatSSE,
} from '../services/api'

function makeSteps(): ThinkingStep[] {
  return [
    { key: 'sql', label: '生成 SQL 查询', status: 'running', startedAt: Date.now() },
    { key: 'exec', label: '执行数据查询', status: 'pending' },
    { key: 'answer', label: 'AI 分析解读', status: 'pending' },
    { key: 'chart', label: '生成可视化图表', status: 'pending' },
  ]
}

function updateStep(
  steps: ThinkingStep[],
  key: string,
  patch: Partial<ThinkingStep>,
): ThinkingStep[] {
  return steps.map((s) => (s.key === key ? { ...s, ...patch } : s))
}

function advanceToStep(steps: ThinkingStep[], targetKey: string): ThinkingStep[] {
  const now = Date.now()
  return steps.map((s) => {
    if (s.key === targetKey) {
      return { ...s, status: 'running', startedAt: s.startedAt ?? now }
    }
    if (s.status === 'running' && s.key !== targetKey) {
      return { ...s, status: 'done', doneAt: now }
    }
    return s
  })
}

function finishAllSteps(steps: ThinkingStep[]): ThinkingStep[] {
  const now = Date.now()
  return steps.map((s) =>
    s.status === 'running' || s.status === 'pending'
      ? { ...s, status: 'done', doneAt: now }
      : s,
  )
}

function patchLastAI(
  messages: Message[],
  updater: (msg: Message) => Message,
): Message[] {
  const msgs = [...messages]
  const last = msgs[msgs.length - 1]
  if (last?.role === 'assistant') {
    msgs[msgs.length - 1] = updater(last)
  }
  return msgs
}

interface SQLEntry {
  sql: string
  timestamp: number
}

interface AppState {
  sessions: Session[]
  currentSessionId: string | null
  messages: Message[]
  charts: ChartConfig[]
  sqlHistory: SQLEntry[]
  isStreaming: boolean
  abortController: AbortController | null

  loadSessions: () => Promise<void>
  setCurrentSession: (id: string) => Promise<void>
  addSession: () => Promise<void>
  deleteSession: (id: string) => Promise<void>
  sendMessage: (content: string) => void
  setIsStreaming: (val: boolean) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  charts: [],
  sqlHistory: [],
  isStreaming: false,
  abortController: null,

  loadSessions: async () => {
    try {
      const sessions = await fetchSessions()
      set({ sessions })
      if (sessions.length > 0 && !get().currentSessionId) {
        await get().setCurrentSession(sessions[0].id)
      }
    } catch (e) {
      console.error('Failed to load sessions', e)
    }
  },

  setCurrentSession: async (id) => {
    set({ currentSessionId: id, messages: [], charts: [], sqlHistory: [] })
    try {
      const detail = await fetchSessionDetail(id)
      const charts: ChartConfig[] = []
      const sqlHistory: SQLEntry[] = []
      for (const msg of detail.messages) {
        if (msg.chart_config) charts.push(msg.chart_config)
        if (msg.sql_query) {
          sqlHistory.push({
            sql: msg.sql_query,
            timestamp: new Date(msg.created_at).getTime(),
          })
        }
      }
      set({ messages: detail.messages, charts, sqlHistory })
    } catch (e) {
      console.error('Failed to load session detail', e)
    }
  },

  addSession: async () => {
    try {
      const session = await createSessionApi()
      set((s) => ({
        sessions: [session, ...s.sessions],
        currentSessionId: session.id,
        messages: [],
        charts: [],
        sqlHistory: [],
      }))
    } catch (e) {
      console.error('Failed to create session', e)
    }
  },

  deleteSession: async (id) => {
    try {
      await deleteSessionApi(id)
      set((s) => {
        const remaining = s.sessions.filter((sess) => sess.id !== id)
        const nextId = remaining[0]?.id ?? null
        return {
          sessions: remaining,
          currentSessionId: s.currentSessionId === id ? nextId : s.currentSessionId,
          messages: s.currentSessionId === id ? [] : s.messages,
          charts: s.currentSessionId === id ? [] : s.charts,
          sqlHistory: s.currentSessionId === id ? [] : s.sqlHistory,
        }
      })
      const state = get()
      if (state.currentSessionId) {
        await state.setCurrentSession(state.currentSessionId)
      }
    } catch (e) {
      console.error('Failed to delete session', e)
    }
  },

  sendMessage: (content: string) => {
    const { currentSessionId, isStreaming } = get()
    if (!currentSessionId || isStreaming) return

    const userMsg: Message = {
      id: `temp-${Date.now()}`,
      session_id: currentSessionId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }

    const aiMsg: Message = {
      id: `temp-ai-${Date.now()}`,
      session_id: currentSessionId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      thinkingSteps: makeSteps(),
    }

    set((s) => ({
      messages: [...s.messages, userMsg, aiMsg],
      isStreaming: true,
    }))

    const controller = sendChatSSE(currentSessionId, content, {
      onSQL: (sql) => {
        set((s) => ({
          messages: patchLastAI(s.messages, (m) => ({
            ...m,
            sql_query: sql,
            thinkingSteps: advanceToStep(
              updateStep(m.thinkingSteps ?? [], 'sql', { detail: sql }),
              'exec',
            ),
          })),
          sqlHistory: [...s.sqlHistory, { sql, timestamp: Date.now() }],
        }))
      },
      onQueryResult: (data) => {
        let rowCount = 0
        try {
          rowCount = JSON.parse(data).length
        } catch { /* ignore */ }
        set((s) => ({
          messages: patchLastAI(s.messages, (m) => ({
            ...m,
            query_result: data,
            thinkingSteps: advanceToStep(
              updateStep(m.thinkingSteps ?? [], 'exec', {
                detail: `查询到 ${rowCount} 条数据`,
              }),
              'answer',
            ),
          })),
        }))
      },
      onAnswer: (chunk) => {
        set((s) => ({
          messages: patchLastAI(s.messages, (m) => ({
            ...m,
            content: m.content + chunk,
          })),
        }))
      },
      onChart: (chart) => {
        set((s) => ({
          messages: patchLastAI(s.messages, (m) => ({
            ...m,
            chart_config: chart,
            thinkingSteps: updateStep(
              advanceToStep(m.thinkingSteps ?? [], 'chart'),
              'chart',
              { status: 'done', doneAt: Date.now(), detail: `${chart.chartType} 图表` },
            ),
          })),
          charts: [...s.charts, chart],
        }))
      },
      onError: (msg) => {
        set((s) => ({
          messages: patchLastAI(s.messages, (m) => {
            const steps = (m.thinkingSteps ?? []).map((step) =>
              step.status === 'running'
                ? { ...step, status: 'error' as const, detail: msg }
                : step,
            )
            return {
              ...m,
              content: m.content || `⚠️ ${msg}`,
              thinkingSteps: steps,
            }
          }),
        }))
      },
      onDone: () => {
        set((s) => ({
          isStreaming: false,
          abortController: null,
          messages: patchLastAI(s.messages, (m) => ({
            ...m,
            thinkingSteps: finishAllSteps(m.thinkingSteps ?? []),
          })),
        }))
        const { currentSessionId: sid } = get()
        if (sid) {
          fetchSessions().then((sessions) => set({ sessions })).catch(() => {})
        }
      },
    })

    set({ abortController: controller })
  },

  setIsStreaming: (val) => set({ isStreaming: val }),
}))
