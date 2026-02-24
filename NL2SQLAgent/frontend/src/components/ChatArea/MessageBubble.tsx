import { useMemo } from 'react'
import { UserOutlined, RobotOutlined, TableOutlined } from '@ant-design/icons'
import { Table } from 'antd'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'
import type { Message } from '../../types'
import { ThinkingProcess } from './ThinkingProcess'
import styles from './styles.module.css'

interface Props {
  message: Message
  isStreaming?: boolean
}

const remarkPlugins = [remarkGfm]

export function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'
  const hasThinking = message.thinkingSteps && message.thinkingSteps.length > 0

  const mdComponents = useMemo<Components>(() => ({
    table: ({ children, ...props }) => (
      <div style={{ overflowX: 'auto', margin: '12px 0' }}>
        <table {...props}>{children}</table>
      </div>
    ),
    th: ({ children, style, ...props }) => (
      <th
        {...props}
        style={{
          ...style,
          textAlign: (style?.textAlign as string) || 'left',
        }}
      >
        {children}
      </th>
    ),
    td: ({ children, style, ...props }) => (
      <td
        {...props}
        style={{
          ...style,
          textAlign: (style?.textAlign as string) || 'left',
        }}
      >
        {children}
      </td>
    ),
  }), [])

  const renderQueryResult = () => {
    if (!message.query_result) return null
    try {
      const data = JSON.parse(message.query_result) as Record<string, unknown>[]
      if (!Array.isArray(data) || data.length === 0) return null
      const columns = Object.keys(data[0]).map((key) => ({
        title: key,
        dataIndex: key,
        key,
        ellipsis: true,
      }))
      return (
        <div className={styles.queryResult}>
          <div className={styles.resultHeader}>
            <TableOutlined /> 查询结果 ({data.length} 行)
          </div>
          <Table
            dataSource={data.map((row, i) => ({ ...row, _key: i }))}
            columns={columns}
            rowKey="_key"
            size="small"
            pagination={data.length > 20 ? { pageSize: 20, size: 'small' } : false}
            scroll={{ x: true }}
          />
        </div>
      )
    } catch {
      return null
    }
  }

  return (
    <div className={`${styles.bubble} ${isUser ? styles.userBubble : styles.aiBubble}`}>
      <div className={styles.avatar}>
        {isUser ? <UserOutlined /> : <RobotOutlined />}
      </div>
      <div className={styles.bubbleContent}>
        {isUser ? (
          <div className={styles.userText}>{message.content}</div>
        ) : (
          <>
            {hasThinking && (
              <ThinkingProcess
                steps={message.thinkingSteps!}
                isStreaming={!!isStreaming}
              />
            )}
            {renderQueryResult()}
            {message.content && (
              <div className={styles.markdownContent}>
                <ReactMarkdown
                  remarkPlugins={remarkPlugins}
                  components={mdComponents}
                >
                  {message.content}
                </ReactMarkdown>
                {isStreaming && (
                  <span className={styles.typingCursor} />
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
