import { useAppStore } from '../../store'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import styles from './styles.module.css'

export function ChatArea() {
  const messages = useAppStore((s) => s.messages)
  const currentSessionId = useAppStore((s) => s.currentSessionId)
  const sendMessage = useAppStore((s) => s.sendMessage)
  const isStreaming = useAppStore((s) => s.isStreaming)

  return (
    <div className={styles.chatArea}>
      <div className={styles.header}>
        <span className={styles.title}>智能数据分析助理</span>
        <span className={styles.subtitle}>自然语言查询数据库，AI 帮你分析</span>
      </div>
      <MessageList messages={messages} isStreaming={isStreaming} />
      <ChatInput onSend={sendMessage} disabled={isStreaming || !currentSessionId} />
    </div>
  )
}
