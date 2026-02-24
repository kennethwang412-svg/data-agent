import { useState, type KeyboardEvent } from 'react'
import { Input, Button } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import styles from './styles.module.css'

const { TextArea } = Input

interface Props {
  onSend: (content: string) => void
  disabled: boolean
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={styles.inputArea}>
      <div className={styles.inputWrapper}>
        <TextArea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的问题，例如：各地区的销售总额是多少？"
          autoSize={{ minRows: 1, maxRows: 4 }}
          disabled={disabled}
          className={styles.textArea}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className={styles.sendBtn}
        />
      </div>
      <div className={styles.inputHint}>Enter 发送，Shift+Enter 换行</div>
    </div>
  )
}
