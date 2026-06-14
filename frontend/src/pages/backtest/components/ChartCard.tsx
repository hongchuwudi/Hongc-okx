/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: ECharts 权益曲线卡片
 */

import ReactECharts from 'echarts-for-react'
import type { ChartCardProps } from '@/types/props/props'

export default function ChartCard({ title, option, key, notMerge = false }: ChartCardProps) {
  return (
    <div className="card bg-base-100 border border-base-300">
      <div className="card-body p-4">
        <h2 className="card-title text-base">{title}</h2>
        <ReactECharts key={key} option={option} style={{ height: 320 }} notMerge={notMerge} className="h-60 md:h-80" />
      </div>
    </div>
  )
}
