/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: KlineChart.tsx K线图表
 * 描述: K 线图组件，支持多时间周期切换，展示 OHLC 蜡烛图、MA 均线和成交量柱状图
 *
 * 包含:
 * - 类型: KlineData — K 线数据点类型
 * - 函数: chartColors — 获取图表配色方案（支持亮/暗主题）
 * - 函数: ma — 计算移动平均线
 * - 组件: KlineChart — K 线图主组件
 */
import { useEffect, useState, useMemo, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import { CandlestickChart, Loader2 } from 'lucide-react'

interface KlineData { time: number; open: number; high: number; low: number; close: number; volume: number }

// 获取图表配色方案（支持亮色/暗色主题自适应）
function chartColors() {
  const dark = document.documentElement.dataset.theme === 'dark'
  return {
    bg: dark ? '#0b1020' : '#ffffff',
    text: dark ? '#8a8a9e' : '#6b6b7b',
    text2: dark ? '#5a5a72' : '#9b9bae',
    border: dark ? '#1f1f3a' : '#e8e8ec',
    green: '#26a69a',
    red: '#ef5350',
    greenBg: dark ? 'rgba(38,166,154,0.2)' : 'rgba(38,166,154,0.15)',
    redBg: dark ? 'rgba(239,83,80,0.2)' : 'rgba(239,83,80,0.15)',
    brand: '#3370FF',
  }
}

// K 线图主组件 — 支持 1m/5m/30m/1h/4h/1d 周期切换，30 秒自动刷新
export default function KlineChart() {
  const [data, setData] = useState<KlineData[]>([])
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState('1h')

  // 获取 K 线数据 — 请求指定周期的 OHLCV 数据
  const fetchData = useCallback(async (tf: string) => {
    setLoading(true)
    try { const res = await fetch(`/api/kline?symbol=BTC/USDT:USDT&timeframe=${tf}&limit=120`); setData(await res.json()) }
    catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchData(timeframe) }, [timeframe, fetchData])
  // 每30秒自动刷新K线
  useEffect(() => {
    const t = setInterval(() => fetchData(timeframe), 30000)
    return () => clearInterval(t)
  }, [timeframe, fetchData])

  const option: EChartsOption = useMemo(() => {
    if (!data.length) return {}
    const c = chartColors()
    const dates = data.map(d => { const dt = new Date(d.time); return dt.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + '\n' + dt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) })
    const ohlc = data.map(d => [d.open, d.close, d.low, d.high])
    const volumes = data.map(d => d.volume)
    const closes = data.map(d => d.close)
    // 计算移动平均线（SMA） — 返回指定周期的均值序列
    function ma(period: number) {
      const r: (number | null)[] = []
      for (let i = 0; i < closes.length; i++) {
        if (i < period - 1) { r.push(null); continue }
        let sum = 0; for (let j = i - period + 1; j <= i; j++) sum += closes[j]
        r.push(Math.round(sum / period * 100) / 100)
      }
      return r
    }
    const ma5 = ma(5); const ma10 = ma(10); const ma30 = ma(30)
    return {
      backgroundColor: 'transparent', animation: false,
      grid: [{ left: 65, right: 16, top: 8, height: '58%' }, { left: 65, right: 16, top: '76%', height: '14%' }],
      xAxis: [
        { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: c.border } }, axisTick: { show: false }, axisLabel: { color: c.text2, fontSize: 10, interval: Math.floor(dates.length / 6) } },
        { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: c.border } }, axisTick: { show: false }, axisLabel: { show: false } },
      ],
      yAxis: [
        { type: 'value', gridIndex: 0, scale: true, position: 'left', splitLine: { lineStyle: { color: c.border, type: 'dashed' } }, axisLabel: { color: c.text, fontSize: 11, formatter: (v: number) => '$' + v.toLocaleString() } },
        { type: 'value', gridIndex: 1, splitLine: { show: false }, axisLabel: { color: c.text2, fontSize: 9, formatter: (v: number) => v >= 1000 ? (v / 1000).toFixed(1) + 'K' : v.toString() } },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], zoomOnMouseWheel: true, moveOnMouseMove: true, start: Math.max(0, 100 - (30 / data.length) * 100), end: 100 },
        { type: 'slider', xAxisIndex: [0, 1], height: 20, bottom: 4, start: Math.max(0, 100 - (30 / data.length) * 100), end: 100, borderColor: c.border, backgroundColor: c.bg, dataBackground: { lineStyle: { color: c.brand }, areaStyle: { color: 'rgba(51,112,255,0.08)' } }, selectedDataBackground: { lineStyle: { color: c.brand }, areaStyle: { color: 'rgba(51,112,255,0.2)' } }, handleStyle: { color: c.brand }, textStyle: { color: c.text2, fontSize: 10 } },
      ],
      tooltip: {
        trigger: 'axis', axisPointer: { type: 'cross' },
        backgroundColor: c.bg, borderColor: c.border, textStyle: { fontSize: 12 },
        formatter: (params: unknown) => {
          const p = params as { axisValue: string; seriesName: string; data: number | number[]; color: string }[]
          if (!p?.length) return ''
          const k = p.find(x => x.seriesName === 'K线')
          const d = k?.data as number[] | undefined
          if (!d) return p[0].axisValue
          const change = d[1] - d[0]; const pct = d[0] > 0 ? (change / d[0] * 100).toFixed(2) : '0'
          const color = change >= 0 ? c.green : c.red
          return `<div style="color:${c.text2}">${p[0].axisValue}</div>
            <div>开 <b>${d[0].toFixed(1)}</b> 高 <b>${d[2].toFixed(1)}</b></div>
            <div>低 <b>${d[3].toFixed(1)}</b> 收 <b style="color:${color}">${d[1].toFixed(1)}</b></div>
            <div style="color:${color}">涨跌 ${change >= 0 ? '+' : ''}${change.toFixed(1)} (${change >= 0 ? '+' : ''}${pct}%)</div>`
        },
      },
      series: [
        { name: 'MA5', type: 'line', data: ma5, smooth: true, symbol: 'none', lineStyle: { color: '#f5a623', width: 1, type: 'solid' } },
        { name: 'MA10', type: 'line', data: ma10, smooth: true, symbol: 'none', lineStyle: { color: '#6ee7ff', width: 1, type: 'solid' } },
        { name: 'MA30', type: 'line', data: ma30, smooth: true, symbol: 'none', lineStyle: { color: '#c9d3ff', width: 1, type: 'solid' } },
        { name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0, data: ohlc, itemStyle: { color: c.green, color0: c.red, borderColor: c.green, borderColor0: c.red }, barWidth: '60%' },
        { name: '量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes, itemStyle: { color: (p: { dataIndex: number }) => { const d = data[p.dataIndex]; return d.close >= d.open ? c.greenBg : c.redBg } } },
      ],
    } as EChartsOption
  }, [data])

  if (loading) return <div className="card-dash bg-base-200 h-full flex items-center justify-center"><Loader2 className="w-5 h-5 animate-spin text-primary" /></div>

  return (
    <div className="card-dash bg-base-200 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2 md:mb-3">
        <div className="flex items-center gap-1.5 md:gap-2">
          <CandlestickChart className="w-[16px] h-[16px] md:w-[18px] md:h-[18px] text-primary" />
          <span className="text-[12px] md:text-[13px] font-semibold text-base-content">BTC/USDT K线</span>
        </div>
        <div className="flex gap-0.5 md:gap-1">
          {['1m', '5m', '30m', '1h', '4h', '1d'].map(tf => (
            <button key={tf} onClick={() => setTimeframe(tf)} className={`px-1.5 md:px-2 py-0.5 md:py-1 text-[10px] md:text-[11px] font-semibold rounded-md transition-colors ${timeframe === tf ? 'bg-primary text-primary-content' : 'bg-transparent text-base-content/60 hover:text-base-content hover:bg-base-300/50'}`}>{tf}</button>
          ))}
        </div>
      </div>
      <div className="flex-1"><ReactECharts option={option} style={{ height: '100%', width: '100%' }} notMerge /></div>
    </div>
  )
}
