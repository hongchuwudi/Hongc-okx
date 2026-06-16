/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: EquityChart.tsx 权益曲线图表
 * 描述: 权益曲线图表，使用 ECharts 展示账户权益随时间变化趋势，含涨跌幅标记
 *
 * 包含:
 * - 类型: Props — 组件属性类型
 * - 函数: c — 获取图表主题色配置
 * - 函数: fmtUSD — 美元金额格式化
 * - 组件: EquityChart — 权益曲线 ECharts 组件
 */
import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import { TrendingUp } from 'lucide-react'
import type { EquityPoint } from '../../types/dashboard'

interface Props { data: EquityPoint[] }

// 获取图表主题色配置（支持亮色/暗色主题）
function c() {
  const dark = document.documentElement.dataset.theme === 'dark'
  return { text: dark ? '#8a8a9e' : '#6b6b7b', text2: dark ? '#5a5a72' : '#9b9bae', border: dark ? '#1f1f3a' : '#e8e8ec', green: '#26a69a', red: '#ef5350', bg: dark ? 'rgba(20,20,37,0.95)' : 'rgba(255,255,255,0.95)' }
}

// 格式化美元金额显示
function fmtUSD(n: number): string { return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2 }) }

// 权益曲线图表组件 — 展示最近 12h 账户权益变化及涨跌幅度
export default function EquityChart({ data }: Props) {
  const { dates, equities, lineColor, delta, deltaPct } = useMemo(() => {
    if (!data?.length) return { dates: [] as string[], equities: [] as number[], lineColor: '#26a69a', delta: 0, deltaPct: 0 }
    const recent = data.slice(-720) // 最近 12h
    if (!recent.length) return { dates: [] as string[], equities: [] as number[], lineColor: '#26a69a', delta: 0, deltaPct: 0 }
    const d = recent[recent.length - 1].equity - recent[0].equity
    return {
      dates: recent.map(p => p.timestamp.length >= 16 ? p.timestamp.substring(5, 16) : p.timestamp),
      equities: recent.map(p => p.equity),
      lineColor: d >= 0 ? '#26a69a' : '#ef5350',
      delta: d, deltaPct: recent[0].equity > 0 ? (d / recent[0].equity * 100) : 0,
    }
  }, [data])

  const option: EChartsOption = useMemo(() => {
    if (!equities.length) return {}
    const cl = c(); const lc = delta >= 0 ? cl.green : cl.red
    const int = Math.max(1, Math.floor(dates.length / 8))
    return {
      backgroundColor: 'transparent',
      grid: { left: 65, right: 16, top: 10, bottom: 28 },
      xAxis: { type: 'category', data: dates, axisLine: { lineStyle: { color: cl.border } }, axisTick: { show: false }, axisLabel: { color: cl.text2, fontSize: 10, interval: int, rotate: 20 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: cl.border, type: 'dashed' } }, axisLabel: { color: cl.text, fontSize: 11, formatter: (v: number) => '$' + v.toLocaleString('en-US', { maximumFractionDigits: 0 }) } },
      tooltip: { trigger: 'axis', backgroundColor: cl.bg, borderColor: cl.border, textStyle: { fontSize: 12 } },
      series: [{ type: 'line', data: equities, smooth: true, symbol: 'none', lineStyle: { color: lc, width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: lc === cl.green ? 'rgba(38,166,154,0.22)' : 'rgba(239,83,80,0.18)' }, { offset: 1, color: 'rgba(0,0,0,0)' }] } } }],
    } as EChartsOption
  }, [equities, dates, delta])

  if (!data?.length) {
    return <div className="card-dash bg-base-200"><div className="flex items-center gap-2"><TrendingUp className="w-[18px] h-[18px] text-base-content/60" /><span className="text-[13px] font-semibold text-base-content">权益曲线</span></div><div className="text-center py-10 text-[13px] text-base-content/40">暂无数据</div></div>
  }

  return (
    <div className="card-dash bg-base-200">
      <div className="flex items-center gap-2 mb-1">
        <TrendingUp className="w-[18px] h-[18px] text-base-content/60" />
        <span className="text-[13px] font-semibold text-base-content">权益曲线 (12h)</span>
        <span className="ml-auto text-[13px] font-semibold" style={{ color: lineColor }}>
          {delta >= 0 ? '+' : ''}{fmtUSD(delta)} ({deltaPct >= 0 ? '+' : ''}{deltaPct.toFixed(2)}%)
        </span>
      </div>
      <ReactECharts option={option} style={{ height: 260, width: '100%' }} notMerge />
    </div>
  )
}
