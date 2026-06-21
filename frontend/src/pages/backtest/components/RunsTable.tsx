/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测历史记录表格 + 分页
 */

import type { RunsTableProps } from '@/types/props/props'
import Paginator from '@/components/common/Paginator'
import { Eye, CheckCircle, XCircle, Clock } from 'lucide-react'

function statusLabel(s: string) {
  if (s === 'completed') return '已完成'
  if (s === 'failed') return '失败'
  if (s === 'running') return '运行中'
  return s
}

export default function RunsTable({ runs, onView, page, pageSize, total, onPageChange }: RunsTableProps) {
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
            {runs.map((r: RunsTableProps['runs'][number]) => (
              <tr key={r.id}>
                <td className="text-xs py-1.5hidden md:table-cell">#{r.id}</td>
                <td className="text-xs py-1.5font-semibold">{r.strategy_name}</td>
                <td className="text-xs">{r.symbol}</td>
                <td className="text-xs py-1.5hidden md:table-cell">{r.timeframe}</td>
                <td className="text-xs py-1.5hidden md:table-cell">{r.data_count}</td>
                <td className={`text-xs py-1.5 font-semibold ${(r.total_return_pct ?? 0) >= 0 ? 'text-success' : 'text-error'}`}>
                  {(r.total_return_pct ?? 0).toFixed(2)}%
                </td>
                <td className="text-xs">{(r.win_rate ?? 0).toFixed(0)}%</td>
                <td className="text-xs py-1.5text-warning hidden md:table-cell">{(r.max_drawdown_pct ?? 0).toFixed(2)}%</td>
                <td className="text-xs py-1.5hidden md:table-cell">{(r.sharpe_ratio ?? 0).toFixed(2)}</td>
                <td>
                  <span className={`badge badge-xs gap-1 ${r.status === 'completed' ? 'badge-success' : r.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                    {r.status === 'completed' ? <CheckCircle size={10} /> : r.status === 'failed' ? <XCircle size={10} /> : <Clock size={10} />}
                    {statusLabel(r.status)}
                  </span>
                </td>
                <td>
                  <button onClick={() => onView(r.id)} className="btn btn-xs btn-ghost gap-1">
                    <Eye size={12} /> 详情
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页条 */}
      <div className="shrink-0 border-t border-base-200 bg-base-100 px-4 py-2">
        <Paginator
          size="small"
          current={page}
          total={total}
          pageSize={pageSize}
          pageSizeOptions={[10, 20, 50]}
          showSizeChanger
          onChange={onPageChange}
        />
      </div>
    </div>
  )
}
