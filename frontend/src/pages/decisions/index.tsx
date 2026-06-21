/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: Agent 决策历史页面 — 分页浏览每次 tick 的 AI 决策记录
 *
 * 包含:
 * - StatsBar — 统计摘要
 * - DecisionTable — 分页决策表格
 */

import { useState, useEffect, useCallback } from 'react'
import { fetchDecisions } from '@/api/agents'
import type { AgentDecision } from '@/types/agents'
import Paginator from '@/components/common/Paginator'
import { Brain } from 'lucide-react'

function fmtTs(ts: string): string {
  const d = new Date(ts.includes('Z') || ts.includes('+') ? ts : ts + 'Z')
  const M = String(d.getMonth() + 1).padStart(2, '0')
  const D = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${M}-${D} ${h}:${m}:${s}`
}

export default function DecisionsPage() {
  const [data, setData] = useState<AgentDecision[]>([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (p: number, ps: number) => {
    setLoading(true)
    try {
      const res = await fetchDecisions(p, ps)
      setData(res.data)
      setTotal(res.total)
      setPage(res.page)
    } catch { /* */ }
    setLoading(false)
  }, [])

  useEffect(() => { load(1, pageSize) }, [load, pageSize])

  const td = 'text-xs py-1.5'

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] px-4 pt-3">
      {/* 统计条 */}
      <div className="flex items-center gap-4 mb-3 bg-base-100 rounded-lg px-4 py-2.5 border border-base-300 shrink-0 text-xs">
        <Brain size={14} className="text-base-content/40" />
        <span className="text-base-content/40">总决策</span>
        <span className="font-mono font-semibold">{total} 次</span>
        <span className="text-base-content/20">|</span>
        <span className="text-base-content/40">当前页</span>
        <span className="font-mono">{page} / {Math.max(1, Math.ceil(total / pageSize))}</span>
      </div>

      {/* 表格 */}
      <div className="flex-1 overflow-auto bg-base-100 rounded-lg border border-base-300">
        <table className="table table-sm table-zebra">
          <thead className="sticky top-0 bg-base-200 z-10">
            <tr>
              <th className="text-xs w-[120px]">时间</th>
              <th className="text-xs w-[70px]">方向</th>
              <th className="text-xs w-[60px]">信心</th>
              <th className="text-xs w-[90px]">模式</th>
              <th className="text-xs w-[100px]">止盈/止损</th>
              <th className="text-xs w-full">理由</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 && !loading && (
              <tr><td colSpan={6} className="text-center text-base-content/30 py-8">暂无决策记录</td></tr>
            )}
            {data.map(d => (
              <tr key={d.id} className="hover:bg-base-200 cursor-pointer">
                <td className={`${td} font-mono text-base-content/50 whitespace-nowrap`}>{fmtTs(d.timestamp)}</td>
                <td className={td}>
                  <span className={`badge badge-xs font-bold ${
                    d.signal === 'BUY' ? 'badge-success' : d.signal === 'SELL' ? 'badge-error' : 'badge-ghost'
                  }`}>
                    {d.signal}
                  </span>
                </td>
                <td className={`${td} text-base-content/50`}>{d.confidence}</td>
                <td className={`${td} text-base-content/50`}>{d.mode}</td>
                <td className={`${td} font-mono`}>
                  <span className="text-success">+{d.take_profit.toFixed(4)}</span>
                  <span className="text-base-content/20"> / </span>
                  <span className="text-error">{d.stop_loss.toFixed(4)}</span>
                </td>
                <td className={`${td} text-base-content/50 truncate max-w-md`}>{d.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      <div className="flex items-center justify-center py-2 shrink-0">
        <Paginator
          size="small"
          current={page}
          total={total}
          pageSize={pageSize}
          pageSizeOptions={[10, 20, 50]}
          showSizeChanger
          onChange={(p, ps) => { setPageSize(ps); load(p, ps) }}
        />
      </div>
    </div>
  )
}
