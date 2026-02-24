import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { Tag } from 'antd'
import type { ChartConfig } from '../../types'
import styles from './styles.module.css'

interface Props {
  chart: ChartConfig
}

const TYPE_LABELS: Record<string, { text: string; color: string }> = {
  bar: { text: 'BAR', color: '#a855f7' },
  line: { text: 'LINE', color: '#00f0ff' },
  pie: { text: 'PIE', color: '#ff00e5' },
  scatter: { text: 'SCATTER', color: '#fbbf24' },
  table: { text: 'TABLE', color: '#555577' },
}

export function ChartRenderer({ chart }: Props) {
  const label = TYPE_LABELS[chart.chartType] ?? { text: chart.chartType, color: '#555577' }

  const themedOption = useMemo(() => ({
    ...chart.option,
    title: { show: false },
    backgroundColor: 'transparent',
    textStyle: { color: '#8888aa', fontFamily: 'Rajdhani, sans-serif' },
    legend: {
      ...(chart.option.legend as object ?? {}),
      textStyle: { color: '#8888aa' },
    },
    xAxis: chart.option.xAxis ? {
      ...(chart.option.xAxis as object),
      axisLine: { lineStyle: { color: 'rgba(0,240,255,0.15)' } },
      axisLabel: { color: '#8888aa', ...(chart.option.xAxis as Record<string, unknown>)?.axisLabel as object },
      splitLine: { lineStyle: { color: 'rgba(0,240,255,0.04)' } },
    } : undefined,
    yAxis: chart.option.yAxis ? {
      ...(chart.option.yAxis as object),
      axisLine: { lineStyle: { color: 'rgba(0,240,255,0.15)' } },
      axisLabel: { color: '#8888aa' },
      splitLine: { lineStyle: { color: 'rgba(0,240,255,0.06)' } },
    } : undefined,
    tooltip: {
      ...(chart.option.tooltip as object ?? {}),
      backgroundColor: 'rgba(13,13,26,0.92)',
      borderColor: 'rgba(0,240,255,0.2)',
      textStyle: { color: '#e0e0ff' },
    },
  }), [chart.option])

  return (
    <div className={styles.chartCard}>
      <div className={styles.chartTitle}>
        {chart.title && <span>{chart.title}</span>}
        <Tag
          className={styles.chartTag}
          style={{ background: `${label.color}20`, color: label.color, borderColor: `${label.color}40` }}
        >
          {label.text}
        </Tag>
      </div>
      <ReactECharts
        option={themedOption}
        style={{ height: 260, width: '100%' }}
        opts={{ renderer: 'svg' }}
      />
    </div>
  )
}
