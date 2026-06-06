import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import { PieChart } from 'lucide-react'
import type { Trade } from '../../types/dashboard'

const COLORS: Record<string, string> = { BUY: '#00b96b', SELL: '#f54c5c', HOLD: '#f5a623' }

export default function SignalDistributionChart({ trades }: { trades: Trade[] }) {
  const pieData = useMemo(() => {
    if (!trades?.length) return []
    const counts: Record<string, number> = {}
    trades.forEach(t => { counts[t.signal || 'HOLD'] = (counts[t.signal || 'HOLD'] || 0) + 1 })
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  }, [trades])

  const option: EChartsOption = useMemo(() => {
    if (!pieData.length) return {}
    const dark = document.documentElement.dataset.theme === 'dark'
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', backgroundColor: dark ? 'rgba(20,20,37,0.95)' : 'rgba(255,255,255,0.95)', borderColor: dark ? '#1f1f3a' : '#e8e8ec', textStyle: { color: dark ? '#e8e8f0' : '#1a1a2e', fontSize: 12 }, formatter: '{b}: {c} ({d}%)' },
      series: [{ type: 'pie', radius: ['55%', '82%'], center: ['50%', '50%'], avoidLabelOverlap: false, itemStyle: { borderColor: dark ? '#0f0f1a' : '#ffffff', borderWidth: 2, borderRadius: 4 }, label: { show: false }, emphasis: { scaleSize: 6 },
        data: pieData.map(d => ({ ...d, itemStyle: { color: COLORS[d.name] || '#3370FF' } })) }],
    } as EChartsOption
  }, [pieData])

  if (!pieData.length) {
    return <div className="card-dash bg-base-200 h-full flex flex-col"><div className="flex items-center gap-2 mb-3"><PieChart className="w-[18px] h-[18px] text-base-content/60" /><span className="text-[13px] font-semibold text-base-content">信号分布</span></div><div className="flex-1 flex items-center justify-center text-[13px] text-base-content/40">暂无数据</div></div>
  }

  return (
    <div className="card-dash bg-base-200 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-1"><PieChart className="w-[18px] h-[18px] text-base-content/60" /><span className="text-[13px] font-semibold text-base-content">信号分布</span></div>
      <ReactECharts option={option} style={{ height: 240, width: '100%' }} notMerge />
      <div className="flex justify-center gap-4 mt-1">
        {pieData.map(d => (
          <div key={d.name} className="flex items-center gap-1.5 text-[12px]">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ background: COLORS[d.name] || '#3370FF' }} />
            <span className="text-base-content/60">{d.name}</span><span className="text-base-content font-semibold">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
