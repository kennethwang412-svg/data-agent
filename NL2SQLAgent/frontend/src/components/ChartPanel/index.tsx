import { useMemo } from 'react'
import { BarChartOutlined, CodeOutlined } from '@ant-design/icons'
import { useAppStore } from '../../store'
import { ChartRenderer } from './ChartRenderer'
import styles from './styles.module.css'

export function ChartPanel() {
  const charts = useAppStore((s) => s.charts)
  const sqlHistory = useAppStore((s) => s.sqlHistory)

  const pairs = useMemo(() => {
    const maxLen = Math.max(sqlHistory.length, charts.length)
    const result: { sql?: string; chart?: (typeof charts)[0]; index: number }[] = []
    for (let i = 0; i < maxLen; i++) {
      result.push({
        sql: sqlHistory[i]?.sql,
        chart: charts[i],
        index: i,
      })
    }
    return result
  }, [sqlHistory, charts])

  const hasContent = sqlHistory.length > 0 || charts.length > 0

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <BarChartOutlined className={styles.headerIcon} />
        <span className={styles.headerTitle}>SQL &amp; Charts</span>
      </div>
      <div className={styles.chartList}>
        {!hasContent ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>📊</div>
            <span className={styles.emptyText}>发起查询后，SQL 和图表将在这里展示</span>
          </div>
        ) : (
          pairs.map((pair) => (
            <div key={pair.index} className={styles.pairGroup}>
              {pair.sql && (
                <div className={styles.sqlCard}>
                  <div className={styles.sqlCardHeader}>
                    <CodeOutlined className={styles.sqlIcon} />
                    <span className={styles.sqlLabel}>SQL</span>
                  </div>
                  <pre className={styles.sqlCode}>{pair.sql}</pre>
                </div>
              )}
              {pair.chart && (
                <ChartRenderer chart={pair.chart} />
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
