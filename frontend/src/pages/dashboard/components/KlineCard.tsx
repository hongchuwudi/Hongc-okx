/**
 * Created: 2026-06-14
 * Author: hongchuwudi
 * Description: 仪表盘K线图卡片 — OKX风格蜡烛图 + MA5/MA20 + 四线参考
 *
 * Contains:
 * - Component: KlineCard — K线图卡片（时间周期/缩放/持仓线/SL/TP/强平线）
 */

import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { useDashboardStore } from '@/stores/dashboardStore'
import { fetchKline } from '@/api/dashboard'
import { fetchRuntimeConfig } from '@/api/config'
import { ZOOM_LEVELS } from '@/constants/KlineChartRate'
import { estLiquidationPrice } from '@/constants/position'
import { TIMEFRAMES } from '@/constants/trading'
import type { KlinePoint } from '@/types/dashboard'

// MA 计算
function calcMA(data: number[], period: number): (number | null)[] {
  const sma: (number | null)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) { sma.push(null); continue }
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) sum += data[j]
    sma.push(sum / period)
  }
  return sma
}

export default function KlineCard({ refreshKey = 0 }: { refreshKey?: number }) {
  const status = useDashboardStore(s => s.status)
  const wsConnected = useDashboardStore(s => s.wsConnected)
  const chartRef = useRef<ReactECharts>(null)
  const [timeframe, setTimeframe] = useState('1m')
  const [zoomIdx, setZoomIdx] = useState(0)
  const [zoomStart, setZoomStart] = useState(0)
  const [zoomEnd, setZoomEnd] = useState(100)
  const [data, setData] = useState<KlinePoint[]>([])
  const [loading, setLoading] = useState(true)
  const refTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const [symbol, setSymbol] = useState('DOGE/USDT:USDT')
  const symbolRef = useRef(symbol)

  const position = status?.position ?? null
  const aiSignal = status?.ai_signal ?? null
  const leverage = status?.account?.leverage ?? 10

  useEffect(() => { symbolRef.current = symbol }, [symbol])

  // 核心刷新：读运行时配置 → 拉 K 线
  const refresh = useCallback(async () => {
    try {
      const cfg = await fetchRuntimeConfig()
      console.log('[KlineCard] runtime符号:', cfg.symbol, '当前symbol:', symbolRef.current)
      // 侧边栏改了 symbol → 立即跟
      if (cfg.symbol && cfg.symbol !== symbolRef.current) {
        console.log('[KlineCard] 切换交易对:', symbolRef.current, '→', cfg.symbol)
        setSymbol(cfg.symbol)
      }
      const displaySymbol = cfg.symbol || symbolRef.current
      const kdata = await fetchKline(displaySymbol, timeframe, 200)
      console.log('[KlineCard] 拉取K线:', displaySymbol, '数据量:', kdata.length)
      setData(kdata)
      setLoading(false)
    } catch (err) {
      console.error('[KlineCard] 刷新失败:', err)
      setLoading(false)
    }
  }, [timeframe])

  // 初始加载 + 周期切换 + symbol 变化 + 配置变更通知
  useEffect(() => { refresh() }, [refresh, symbol, refreshKey])

  // 每 10 秒轮询最新数据
  useEffect(() => {
    refTimer.current = setInterval(refresh, 10_000)
    return () => { if (refTimer.current) clearInterval(refTimer.current) }
  }, [refresh])

  // 缩放
  const handleZoom = useCallback((idx: number) => {
    const el = chartRef.current?.getEchartsInstance()
    setZoomIdx(idx)
    const z = ZOOM_LEVELS[idx]
    setZoomStart(z.start)
    setZoomEnd(z.end)
    if (el) el.dispatchAction({ type: 'dataZoom', start: z.start, end: z.end })
  }, [])

  // 降采样到 500 根以内
  const step = Math.ceil(data.length / 500)
  const sampled = step > 1 ? data.filter((_, i) => i % step === 0) : data

  const times = sampled.map(d => d.time)
  const closes = sampled.map(d => d.close)
  const ma5 = calcMA(closes, 5)
  const ma20 = calcMA(closes, 20)

  const candlestickData = sampled.map(d => [d.time, d.open, d.close, d.low, d.high] as [number, number, number, number, number])
  const ma5Data = sampled.map((d, i) => [d.time, ma5[i]] as [number, number | null])
  const ma20Data = sampled.map((d, i) => [d.time, ma20[i]] as [number, number | null])

  const spanMs = sampled.length > 1 ? Math.max(...times) - Math.min(...times) : 0

  // ── 四线参考：强平 / 入场 / 止损 / 止盈 ──
  function valid(v: unknown): v is number {
    return typeof v === 'number' && Number.isFinite(v) && v > 0
  }

  function hLine(y: number, label: string, color: string, dash: 'solid' | 'dashed' | 'dotted') {
    return [
      { xAxis: 'min', yAxis: y, lineStyle: { type: dash, color, width: 3 }, label: { show: true, formatter: label, position: 'start', fontSize: 11, color, fontWeight: 'bold' } },
      { xAxis: 'max', yAxis: y },
    ]
  }

  const markLines: unknown[] = []

  if (position && valid(position.entry_price)) {
    const liq = estLiquidationPrice(position.entry_price, leverage, position.side)
    const entry = position.entry_price
    const sl = aiSignal?.stop_loss
    const tp = aiSignal?.take_profit

    if (valid(liq)) markLines.push(hLine(liq, '强平', '#9ca3af', 'dotted'))
    markLines.push(hLine(entry, '开仓', '#fbbf24', 'solid'))
    if (valid(sl)) markLines.push(hLine(sl, '止损', '#ef4444', 'dashed'))
    if (valid(tp)) markLines.push(hLine(tp, '止盈', '#22c55e', 'dashed'))
  }

  // 缓存 ECharts option，只在数据/持仓变化时重建
  const option = useMemo(() => ({
    grid: [
      { left: 12, right: 60, top: 16, bottom: 24 },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, zoomOnMouseWheel: true, moveOnMouseMove: true, start: zoomStart, end: zoomEnd },
    ],
    xAxis: [
      {
        type: 'time', axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisTick: { show: false },
        axisLabel: {
          fontSize: 10, color: '#9ca3af',
          formatter: (v: number) => {
            const d = new Date(v)
            const HH = String(d.getHours()).padStart(2, '0')
            const MM = String(d.getMinutes()).padStart(2, '0')
            if (spanMs < 3600_000) return `${HH}:${MM}`
            const md = `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
            if (spanMs < 86400_000) return `${md} ${HH}:${MM}`
            return `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
          },
        },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        type: 'value', scale: true, position: 'right',
        axisLabel: { fontSize: 10, color: '#9ca3af' },
        splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' as const } },
        axisLine: { show: false },
      },
    ],
    series: [
      // MA5
      {
        type: 'line', data: ma5Data,
        smooth: false, symbol: 'none',
        lineStyle: { color: '#f59e0b', width: 1, opacity: 0.8 },
      },
      // MA20
      {
        type: 'line', data: ma20Data,
        smooth: false, symbol: 'none',
        lineStyle: { color: '#a855f7', width: 1, opacity: 0.8 },
      },
      // 蜡烛
      {
        type: 'candlestick', data: candlestickData,
        barMaxWidth: 16,
        itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e' },
        markLine: markLines.length > 0
          ? { animation: false, data: markLines }
          : undefined,
      },
    ],
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross' },
      backgroundColor: '#fff', borderColor: '#e5e7eb',
      textStyle: { fontSize: 11, color: '#374151' },
      formatter: (params: { value: [number, ...number[]]; seriesType: string; seriesName: string }[]) => {
        const d = params.find(p => p.seriesType === 'candlestick')?.value
        if (!d) return ''
        const ts = new Date(d[0]).toLocaleString('zh-CN')
        return `<div style="font-size:11px">${ts}<br/>开: <b>${d[1]}</b>  收: <b>${d[2]}</b>  低: <b>${d[3]}</b>  高: <b>${d[4]}</b></div>`
      },
    },
  }), [data, position, aiSignal?.stop_loss, aiSignal?.take_profit, spanMs, zoomStart, zoomEnd])

  return (
    <div className="card bg-base-100 border border-base-300 h-full">
      <div className="card-body p-3 flex flex-col" style={{ height: '100%' }}>
        {/* 顶部控制栏 */}
        <div className="flex items-center justify-between mb-1 shrink-0">
          {/* 时间周期 — OKX 小药丸风格 */}
          <div className="flex gap-0.5">
            {TIMEFRAMES.map(tf => (
              <button
                key={tf.value}
                onClick={() => setTimeframe(tf.value)}
                className={`btn btn-xs text-xs px-2 h-6 min-h-0 ${
                  timeframe === tf.value
                    ? 'btn-primary'
                    : 'btn-ghost text-base-content/50 hover:text-base-content'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          {/* MA 图例 */}
          <div className="flex items-center gap-3 text-[10px] text-base-content/40">
            <span><span className="inline-block w-3 h-0.5 bg-amber-500 align-middle mr-1" />MA5</span>
            <span><span className="inline-block w-3 h-0.5 bg-purple-500 align-middle mr-1" />MA20</span>
          </div>

          {/* 缩放 */}
          <div className="flex gap-0.5">
            {ZOOM_LEVELS.map((z, i) => (
              <button
                key={z.label}
                onClick={() => handleZoom(i)}
                className={`btn btn-xs text-xs px-1.5 h-6 min-h-0 ${
                  zoomIdx === i ? 'btn-primary' : 'btn-ghost text-base-content/50 hover:text-base-content'
                }`}
              >
                {z.label}
              </button>
            ))}
          </div>
        </div>

        {/* K线图 / 加载中 */}
        {loading && data.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <span className="loading loading-spinner loading-sm" />
          </div>
        ) : (
          <ReactECharts
            ref={chartRef}
            key={symbol + timeframe}
            option={option}
            style={{ flex: 1, minHeight: 0 }}
            notMerge={true}
            opts={{ locale: 'ZH' }}
          />
        )}
      </div>
    </div>
  )
}
