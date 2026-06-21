/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测参数说明面板 — daisyUI modal 实现
 *
 * 包含:
 * - 组件: ParamDrawer — 参数说明弹窗
 */

import { PARAMS } from '@/constants/backtestHelp'

interface Props {
  open: boolean
  onClose: () => void
}

export default function ParamDrawer({ open, onClose }: Props) {
  if (!open) return null

  return (
    <dialog open className="modal modal-open">
      {/* 面板内容 — 靠右对齐 */}
      <div className="modal-box mr-4 w-80 max-w-[85vw] animate-[slideLeft_0.2s_ease-out]">
        <form method="dialog">
          <button
            type="button"
            onClick={onClose}
            className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
          >
            X
          </button>
        </form>

        <h3 className="text-base font-semibold mb-4">参数说明</h3>

        <div className="space-y-4">
          {PARAMS.map(p => (
            <div key={p.title}>
              <div className="text-sm font-semibold">{p.title}</div>
              <div className="text-xs text-base-content/60 mt-0.5">{p.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 点击遮罩关闭 */}
      <form method="dialog" className="modal-backdrop">
        <button type="button" onClick={onClose}>close</button>
      </form>
    </dialog>
  )
}
