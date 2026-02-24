import { DeleteOutlined, MessageOutlined } from '@ant-design/icons'
import type { Session } from '../../types'
import styles from './styles.module.css'

interface Props {
  session: Session
  isActive: boolean
  onSelect: () => void
  onDelete: () => void
}

export function SessionItem({ session, isActive, onSelect, onDelete }: Props) {
  const time = new Date(session.updated_at).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div
      className={`${styles.sessionItem} ${isActive ? styles.active : ''}`}
      onClick={onSelect}
    >
      <div className={styles.sessionContent}>
        <MessageOutlined className={styles.sessionIcon} />
        <div className={styles.sessionText}>
          <span className={styles.sessionTitle}>
            {session.title}
          </span>
          <span className={styles.sessionTime}>
            {time}
          </span>
        </div>
      </div>
      <DeleteOutlined
        className={styles.deleteBtn}
        onClick={(e) => {
          e.stopPropagation()
          onDelete()
        }}
      />
    </div>
  )
}
