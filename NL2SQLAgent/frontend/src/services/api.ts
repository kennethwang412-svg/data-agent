import type { Session, Message, ChartConfig } from '../types'

const BASE = '/api'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '请求失败')
  }
  return res.json()
}

// ---------- Sessions ----------

export async function fetchSessions(): Promise<Session[]> {
  return request<Session[]>('/sessions')
}

export async function createSession(title = '新对话'): Promise<Session> {
  return request<Session>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
}

export async function fetchSessionDetail(
  id: string,
): Promise<{ session: Session; messages: Message[] }> {
  return request(`/sessions/${id}`)
}

export async function deleteSessionApi(id: string): Promise<void> {
  await fetch(`${BASE}/sessions/${id}`, { method: 'DELETE' })
}

// ---------- SSE Chat ----------

export interface SSECallbacks {
  onSQL?: (sql: string) => void
  onQueryResult?: (data: string) => void
  onAnswer?: (chunk: string) => void
  onChart?: (chart: ChartConfig) => void
  onError?: (msg: string) => void
  onDone?: () => void
}

export function sendChatSSE(
  sessionId: string,
  message: string,
  callbacks: SSECallbacks,
): AbortController {
  const controller = new AbortController()

  fetch(`${BASE}/chat/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        callbacks.onError?.(err.detail ?? '请求失败')
        callbacks.onDone?.()
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const dispatch = (event: string, data: string) => {
        switch (event) {
          case 'sql':
            callbacks.onSQL?.(data)
            break
          case 'query_result':
            callbacks.onQueryResult?.(data)
            break
          case 'answer':
            callbacks.onAnswer?.(data)
            break
          case 'chart':
            try {
              callbacks.onChart?.(JSON.parse(data))
            } catch { /* ignore invalid chart json */ }
            break
          case 'error':
            callbacks.onError?.(data)
            break
          case 'done':
            callbacks.onDone?.()
            break
        }
      }

      let currentEvent = ''
      let dataLines: string[] = []
      let doneReceived = false

      const processLine = (line: string) => {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          const afterColon = line.slice(5)
          dataLines.push(afterColon.startsWith(' ') ? afterColon.slice(1) : afterColon)
        } else if (line === '' || line.trim() === '') {
          if (currentEvent && dataLines.length > 0) {
            if (currentEvent === 'done') doneReceived = true
            dispatch(currentEvent, dataLines.join('\n'))
          }
          currentEvent = ''
          dataLines = []
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          processLine(line)
        }
      }

      if (buffer.trim()) {
        processLine(buffer)
      }
      processLine('')

      if (currentEvent && dataLines.length > 0) {
        if (currentEvent === 'done') doneReceived = true
        dispatch(currentEvent, dataLines.join('\n'))
      }

      if (!doneReceived) callbacks.onDone?.()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError?.(err.message)
        callbacks.onDone?.()
      }
    })

  return controller
}
