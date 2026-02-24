import { useEffect } from 'react'
import { PlusOutlined } from '@ant-design/icons'
import { Button } from 'antd'
import { useAppStore } from '../../store'
import { SessionItem } from './SessionItem'
import styles from './styles.module.css'

export function ChatSidebar() {
  const sessions = useAppStore((s) => s.sessions)
  const currentSessionId = useAppStore((s) => s.currentSessionId)
  const addSession = useAppStore((s) => s.addSession)
  const deleteSession = useAppStore((s) => s.deleteSession)
  const setCurrentSession = useAppStore((s) => s.setCurrentSession)
  const loadSessions = useAppStore((s) => s.loadSessions)

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  return (
    <div className={styles.sidebar}>
      <div className={styles.header}>
        <span className={styles.headerTitle}>Sessions</span>
        <Button
          icon={<PlusOutlined />}
          size="small"
          onClick={addSession}
          className={styles.newBtn}
        >
          新对话
        </Button>
      </div>
      <div className={styles.list}>
        {sessions.map((session) => (
          <SessionItem
            key={session.id}
            session={session}
            isActive={session.id === currentSessionId}
            onSelect={() => setCurrentSession(session.id)}
            onDelete={() => deleteSession(session.id)}
          />
        ))}
        {sessions.length === 0 && (
          <div className={styles.empty}>
            <span>暂无对话，点击上方新建</span>
          </div>
        )}
      </div>
    </div>
  )
}
