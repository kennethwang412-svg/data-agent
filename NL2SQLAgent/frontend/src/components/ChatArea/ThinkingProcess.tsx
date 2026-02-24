import { useState, useEffect } from 'react'
import {
  CheckCircleFilled,
  LoadingOutlined,
  ClockCircleOutlined,
  ExclamationCircleFilled,
  DownOutlined,
} from '@ant-design/icons'
import type { ThinkingStep } from '../../types'
import styles from './thinking.module.css'

interface Props {
  steps: ThinkingStep[]
  isStreaming: boolean
}

export function ThinkingProcess({ steps, isStreaming }: Props) {
  const [expanded, setExpanded] = useState(true)
  const [, setTick] = useState(0)

  useEffect(() => {
    if (!isStreaming) return
    const id = setInterval(() => setTick((t) => t + 1), 500)
    return () => clearInterval(id)
  }, [isStreaming])

  const doneCount = steps.filter((s) => s.status === 'done').length
  const allDone = doneCount === steps.length && !isStreaming
  const currentStep = steps.find((s) => s.status === 'running')

  const formatDuration = (step: ThinkingStep) => {
    if (!step.startedAt) return ''
    const end = step.doneAt ?? Date.now()
    const ms = end - step.startedAt
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const statusIcon = (step: ThinkingStep) => {
    switch (step.status) {
      case 'done':
        return <CheckCircleFilled className={styles.iconDone} />
      case 'running':
        return <LoadingOutlined spin className={styles.iconRunning} />
      case 'error':
        return <ExclamationCircleFilled className={styles.iconError} />
      default:
        return <ClockCircleOutlined className={styles.iconPending} />
    }
  }

  return (
    <div className={styles.container}>
      <div
        className={styles.header}
        onClick={() => setExpanded(!expanded)}
      >
        <div className={styles.headerLeft}>
          {isStreaming ? (
            <LoadingOutlined spin className={styles.headerSpinner} />
          ) : (
            <CheckCircleFilled className={styles.headerDoneIcon} />
          )}
          <span className={styles.headerText}>
            {isStreaming
              ? currentStep?.label ?? '处理中...'
              : `分析完成 · ${doneCount} 个步骤`}
          </span>
        </div>
        <DownOutlined
          className={`${styles.arrow} ${expanded ? styles.arrowUp : ''}`}
        />
      </div>

      {expanded && (
        <div className={styles.stepList}>
          {steps.map((step) => (
            <div
              key={step.key}
              className={`${styles.step} ${styles[`step_${step.status}`]}`}
            >
              <div className={styles.stepIcon}>{statusIcon(step)}</div>
              <div className={styles.stepBody}>
                <div className={styles.stepLabel}>{step.label}</div>
                {step.detail && (
                  <div className={styles.stepDetail}>{step.detail}</div>
                )}
              </div>
              {step.startedAt && (
                <div className={styles.stepTime}>{formatDuration(step)}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {allDone && !expanded && (
        <div className={styles.collapsedHint}>
          点击展开查看详细过程
        </div>
      )}
    </div>
  )
}
