/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: KpiCard.tsx KPI卡片组件
 * 描述: KPI 指标卡片组件，用于仪表盘展示单项核心指标值及变化幅度
 *
 * 包含:
 * - 类型: Props — KPI 卡片属性类型（图标/标签/数值/变化量）
 * - 组件: KpiCard — 指标卡片组件
 */
import type { ComponentType } from 'react'

interface Props {
  icon: ComponentType<{ className?: string }>; iconBg: string
  label: string; value: string; delta?: string; deltaUp?: boolean
}

// KPI 指标卡片 — 展示图标、标签、数值和可选的变化量/方向
export default function KpiCard({ icon: Icon, iconBg, label, value, delta, deltaUp }: Props) {
  return (
    <div className="card-dash bg-base-200 flex items-center gap-2.5 px-3 py-2.5">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${iconBg}`}>
        <Icon className="w-[15px] h-[15px]" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[10px] font-medium text-base-content/40 truncate">{label}</div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-[16px] font-bold text-base-content tabular-nums leading-tight">{value}</span>
          {delta && (
            <span className={`text-[11px] font-semibold ${deltaUp === true ? 'text-success' : deltaUp === false ? 'text-error' : 'text-base-content/40'}`}>
              {delta}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
