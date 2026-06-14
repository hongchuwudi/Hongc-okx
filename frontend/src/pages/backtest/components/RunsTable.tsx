/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测历史记录表格 + 分页
 */

import type { RunsTableProps } from '@/types/props'

function statusLabel(s: string) {
  if (s === 'completed') return '已完成'
  if (s === 'failed') return '失败'
  if (s === 'running') return '运行中'
  return s
}

export default function RunsTable({ runs, onView, page, pageSize, totalPages, total, onPageChange }: RunsTableProps) {
  if (runs.length === 0) {
    return <p className="text-sm text-base-content/50 py-8 text-center">暂无回测记录，请先执行一次回测</p>
  }
  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex-1 overflow-auto min-h-0">
        <table className="table table-sm table-zebra">
          <thead>
            <tr>
              <th className="hidden md:table-cell">ID</th>
              <th>策略</th>
              <th>交易对</th>
              <th className="hidden md:table-cell">周期</th>
              <th className="hidden md:table-cell">数据量</th>
              <th>收益率</th>
              <th>胜率</th>
              <th className="hidden md:table-cell">最大回撤</th>
              <th className="hidden md:table-cell">夏普</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {runs.map(r => (
              <tr key={r.id}>
                <td className="text-xs hidden md:table-cell">#{r.id}</td>
                <td className="text-xs font-semibold">{r.strategy_name}</td>
                <td className="text-xs">{r.symbol}</td>
                <td className="text-xs hidden md:table-cell">{r.timeframe}</td>
                <td className="text-xs hidden md:table-cell">{r.data_count}</td>
                <td className={`text-xs font-semibold ${(r.total_return_pct ?? 0) >= 0 ? 'text-success' : 'text-error'}`}>
                  {(r.total_return_pct ?? 0).toFixed(2)}%
                </td>
                <td className="text-xs">{(r.win_rate ?? 0).toFixed(0)}%</td>
                <td className="text-xs text-warning hidden md:table-cell">{(r.max_drawdown_pct ?? 0).toFixed(2)}%</td>
                <td className="text-xs hidden md:table-cell">{(r.sharpe_ratio ?? 0).toFixed(2)}</td>
                <td>
                  <span className={`badge badge-xs ${r.status === 'completed' ? 'badge-success' : r.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                    {statusLabel(r.status)}
                  </span>
                </td>
                <td>
                  <button onClick={() => onView(r.id)} className="btn btn-xs btn-ghost">详情</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页条 */}
      <div className="shrink-0 flex items-center justify-between pt-2 border-t border-base-200 text-xs bg-base-100">
        <div className="flex items-center gap-1.5 whitespace-nowrap">
          <span className="text-base-content/50">共 {total} 条</span>
          <select
            value={pageSize}
            onChange={e => onPageChange(1, Number(e.target.value))}
            className="select select-xs select-ghost"
          >
            <option value={10}>10条/页</option>
            <option value={20}>20条/页</option>
            <option value={50}>50条/页</option>
          </select>
        </div>
        <div className="flex items-center gap-1 whitespace-nowrap">
          <button disabled={page <= 1} onClick={() => onPageChange(page - 1, pageSize)} className="btn btn-xs btn-ghost">上一页</button>
          <span className="px-1">{page}/{totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => onPageChange(page + 1, pageSize)} className="btn btn-xs btn-ghost">下一页</button>
        </div>
      </div>
    </div>
  )
}
