/**
 * Created: 2026-06-14
 * Author: hongchuwudi
 * Description: K线蜡烛图 — OHLCV + 交易标记 + 缩放控制
 */

import { useRef, useState, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { KlineChartProps, MarkPointItem } from '@/types/props/props'
import { ZOOM_LEVELS } from '@/constants/KlineChartRate'

export default function KlineChart({ data, trades }: KlineChartProps) {
  const chartRef = useRef<ReactECharts>(null)
  const [zoomIdx, setZoomIdx] = useState(0)

  const handleZoom = useCallback((idx: number) => {
    const el = chartRef.current?.getEchartsInstance()
    if (!el) return
    setZoomIdx(idx)
    const z = ZOOM_LEVELS[idx]
    el.dispatchAction({ type: 'dataZoom', start: z.start, end: z.end })
  }, [])

  if (data.length === 0) return null

  // 降采样
  const step = Math.ceil(data.length / 500)
  const sampled = step > 1 ? data.filter((_, i) => i % step === 0) : data

  const candlestickData = sampled.map((d) => [d.t, d.o, d.c, d.l, d.h] as [number, number, number, number, number])
  const volumeData = sampled.map((d) => [d.t, d.v, d.c >= d.o ? 1 : -1] as [number, number, number])

  // 交易标记
  const markPointData: MarkPointItem[] = []

  if (trades && data.length > 0) {
    for (const t of trades) {
      const entryIdx = t.bar - t.bars_held
      const exitIdx = t.bar
      if (entryIdx >= 0 && entryIdx < data.length && exitIdx < data.length) {
        const entryBar = data[entryIdx]
        const exitBar = data[exitIdx]
        const isLong = t.side === 'long'
        const color = isLong ? '#16a34a' : '#dc2626'
        const bg = isLong ? 'rgba(22,163,74,0.9)' : 'rgba(220,38,38,0.9)'

        markPointData.push({
          coord: [entryBar.t, isLong ? entryBar.l * 0.998 : entryBar.h * 1.002],
          name: 'entry',
          symbol: 'triangle',
          symbolSize: 14,
          symbolRotate: isLong ? 0 : 180,
          itemStyle: { color, borderColor: '#fff', borderWidth: 1 },
          label: {
            show: true,
            formatter: isLong ? '开多' : '开空',
            position: isLong ? 'bottom' : 'top',
            distance: 10,
            fontSize: 11, fontWeight: 'bold', color: '#fff',
            backgroundColor: bg, borderRadius: 3, padding: [3, 6],
          },
        })

        markPointData.push({
          coord: [exitBar.t, isLong ? exitBar.h * 1.002 : exitBar.l * 0.998],
          name: 'exit',
          symbol: 'pin',
          symbolSize: 22,
          itemStyle: { color: '#f59e0b', borderColor: '#fff', borderWidth: 1 },
          label: {
            show: true,
            formatter: '平仓',
            position: isLong ? 'top' : 'bottom',
            distance: 8,
            fontSize: 11, fontWeight: 'bold', color: '#fff',
            backgroundColor: 'rgba(245,158,11,0.9)', borderRadius: 3, padding: [3, 6],
          },
        })
      }
    }
  }

  const spanMs = sampled.length > 1 ? Math.max(...sampled.map(d => d.t)) - Math.min(...sampled.map(d => d.t)) : 0

  const option = {
    grid: [
      { left: 60, right: 20, top: 20, height: '65%' },
      { left: 60, right: 20, top: '78%', height: '14%' },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], zoomOnMouseWheel: true, moveOnMouseMove: true },
    ],
    xAxis: [
      {
        type: 'time',
        axisLabel: {
          fontSize: 10,
          formatter: (v: number) => {
            const d = new Date(v)
            const HH = String(d.getHours()).padStart(2, '0')
            const MM = String(d.getMinutes()).padStart(2, '0')
            const md = `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
            if (spanMs < 3600_000) return `${HH}:${MM}`
            if (spanMs < 86400_000) return `${HH}:${MM}`
            return `${md} ${HH}:${MM}`
          },
        },
        splitLine: { show: false },
      },
      { type: 'time', gridIndex: 1, axisLabel: { show: false }, splitLine: { show: false } },
    ],
    yAxis: [
      { type: 'value', scale: true, axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
      { type: 'value', gridIndex: 1, axisLabel: { show: false }, splitLine: { show: false } },
    ],
    series: [
      {
        type: 'candlestick', data: candlestickData,
        itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e' },
        markPoint: markPointData.length > 0 ? { data: markPointData, animation: false } : undefined,
      },
      {
        type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumeData,
        itemStyle: { color: (p: { data: [number, number, number] }) => p.data[2] > 0 ? '#ef4444' : '#22c55e' },
      },
    ],
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross' },
      formatter: (params: { value: [number, ...number[]]; seriesType: string }[]) => {
        const d = params.find(p => p.seriesType === 'candlestick')?.value
        if (!d) return ''
        const ts = new Date(d[0]).toLocaleString()
        return `${ts}<br/>开: ${d[1]}  收: ${d[2]}  低: ${d[3]}  高: ${d[4]}`
      },
    },
  }

  return (
    <div className="relative">
      {/* 右上角缩放按钮 */}
      <div className="absolute top-1 right-2 z-10 flex gap-1">
        {ZOOM_LEVELS.map((z, i) => (
          <button
            key={z.label}
            onClick={() => handleZoom(i)}
            className={`btn btn-xs ${zoomIdx === i ? 'btn-primary' : 'btn-ghost'}`}
          >
            {z.label}
          </button>
        ))}
      </div>
      <ReactECharts ref={chartRef} option={option} style={{ height: 370 }} notMerge={false} />
    </div>
  )
}
