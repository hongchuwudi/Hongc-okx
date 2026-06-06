import type { ComponentType } from 'react'

interface Props {
  icon: ComponentType<{ className?: string }>; iconBg: string
  label: string; value: string; delta?: string; deltaUp?: boolean
}

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
