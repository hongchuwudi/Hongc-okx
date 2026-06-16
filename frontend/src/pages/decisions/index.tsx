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
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (p: number) => {
    setLoading(true)
    try {
      const res = await fetchDecisions(p, 15)
      setData(res.data)
      setTotal(res.total)
      setTotalPages(res.total_pages)
      setPage(res.page)
    } catch { /* */ }
    setLoading(false)
  }, [])

  useEffect(() => { load(1) }, [load])

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] px-4 py-3">
      {/* 统计条 */}
      <div className="flex items-center gap-4 mb-3 bg-base-100 rounded-lg px-4 py-2.5 border border-base-300 shrink-0 text-xs">
        <span className="text-base-content/40">总决策</span>
        <span className="font-mono font-semibold">{total} 次</span>
        <span className="text-base-content/20">|</span>
        <span className="text-base-content/40">当前页</span>
        <span className="font-mono">{page} / {totalPages}</span>
      </div>

      {/* 表格 */}
      <div className="flex-1 overflow-auto bg-base-100 rounded-lg border border-base-300">
        <table className="table table-xs table-zebra">
          <thead className="sticky top-0 bg-base-200 z-10">
            <tr>
              <th className="text-[11px] w-[120px]">时间</th>
              <th className="text-[11px] w-[70px]">方向</th>
              <th className="text-[11px] w-[60px]">信心</th>
              <th className="text-[11px] w-[90px]">模式</th>
              <th className="text-[11px] w-[100px]">止盈/止损</th>
              <th className="text-[11px] w-full">理由</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 && !loading && (
              <tr><td colSpan={6} className="text-center text-base-content/30 py-8">暂无决策记录</td></tr>
            )}
            {data.map(d => (
              <tr key={d.id} className="hover:bg-base-200 cursor-pointer">
                <td className="text-[11px] font-mono text-base-content/50 whitespace-nowrap">{fmtTs(d.timestamp)}</td>
                <td>
                  <span className={`badge badge-xs font-bold ${
                    d.signal === 'BUY' ? 'badge-success' : d.signal === 'SELL' ? 'badge-error' : 'badge-ghost'
                  }`}>
                    {d.signal}
                  </span>
                </td>
                <td className="text-[11px] text-base-content/50">{d.confidence}</td>
                <td className="text-[11px] text-base-content/50">{d.mode}</td>
                <td className="text-[11px] font-mono">
                  <span className="text-success">+{d.take_profit.toFixed(4)}</span>
                  <span className="text-base-content/20"> / </span>
                  <span className="text-error">{d.stop_loss.toFixed(4)}</span>
                </td>
                <td className="text-[11px] text-base-content/50 truncate max-w-md">{d.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      <div className="flex items-center justify-center gap-2 py-2 shrink-0">
        <button className="btn btn-xs btn-ghost" disabled={page <= 1} onClick={() => load(page - 1)}>上一页</button>
        <span className="text-xs text-base-content/40">{page} / {totalPages}</span>
        <button className="btn btn-xs btn-ghost" disabled={page >= totalPages} onClick={() => load(page + 1)}>下一页</button>
      </div>
    </div>
  )
}
