/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: PerformanceStats.tsx 绩效统计卡片
 * 描述: 绩效统计面板，展示总盈亏、胜率和总交易数三项核心绩效指标
 *
 * 包含:
 * - 组件: PerformanceStats — 绩效统计卡片组件
 */
import { Trophy } from 'lucide-react'
import type { Performance } from '../types/dashboard'

// 绩效统计卡片 — 展示总盈亏、胜率和总交易数三项核心指标
export default function PerformanceStats({ performance }: { performance: Performance }) {
  const { total_pnl, win_rate, total_trades } = performance
  return (
    <div className="card-dash bg-base-200 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <Trophy className="w-[18px] h-[18px] text-base-content/60" />
        <span className="text-[13px] font-semibold text-base-content">绩效统计</span>
      </div>
      <div className="grid grid-cols-3 gap-3 flex-1">
        {[
          { label: '总盈亏', value: `${total_pnl >= 0 ? '+' : ''}${total_pnl.toFixed(2)}`, color: total_pnl >= 0 ? 'text-success' : 'text-error' },
          { label: '胜率', value: `${win_rate.toFixed(1)}%`, color: win_rate >= 50 ? 'text-success' : 'text-error' },
          { label: '总交易', value: `${total_trades}`, color: 'text-primary' },
        ].map(item => (
          <div key={item.label} className="text-center py-2.5 md:py-3 rounded-xl bg-base-100 border border-base-300">
            <div className="text-[9px] md:text-[10px] text-base-content/40 font-semibold uppercase tracking-wider mb-1 md:mb-1.5">{item.label}</div>
            <div className={`text-[17px] md:text-[20px] font-bold tabular-nums ${item.color}`}>{item.value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
