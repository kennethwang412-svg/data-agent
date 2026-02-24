import { useEffect, useRef } from 'react'
import { MessageBubble } from './MessageBubble'
import type { Message } from '../../types'
import styles from './styles.module.css'

interface Props {
  messages: Message[]
  isStreaming?: boolean
}

export function MessageList({ messages, isStreaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className={styles.emptyMessages}>
        <div className={styles.emptyIcon}>💬</div>
        <div className={styles.emptyTitle}>开始对话</div>
        <div className={styles.emptyHint}>试试问：各地区的销售总额是多少？</div>
      </div>
    )
  }

  return (
    <div className={styles.messageList}>
      {messages.map((msg, idx) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          isStreaming={isStreaming && idx === messages.length - 1}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
