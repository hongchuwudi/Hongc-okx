/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测参数说明右侧抽屉
 */
import { PARAMS } from '@/constants/backtestHelp'
interface Props {
  open: boolean
  onClose: () => void
}

export default function ParamDrawer({ open, onClose }: Props) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-80 max-w-[85vw] bg-base-100 h-full overflow-y-auto shadow-xl animate-[slideLeft_0.2s_ease-out]">
        <div className="p-5 space-y-4">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold">参数说明</h3>
            <button onClick={onClose} className="btn btn-ghost btn-xs btn-circle ml-auto">✕</button>
          </div>
          {PARAMS.map(p => (
            <div key={p.title}>
              <div className="text-sm font-semibold text-base-content">{p.title}</div>
              <div className="text-xs text-base-content/60 mt-0.5">{p.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}