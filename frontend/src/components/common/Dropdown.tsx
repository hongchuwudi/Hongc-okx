/**
 * 创建时间: 2026-06-17
 * 作者: hongchuwudi
 * 描述: 通用下拉菜单 — daisyUI dropdown（CSS focus-within 驱动）
 *
 * 包含:
 * - 组件: Dropdown — 点击弹出选项菜单
 * - 类型: DropdownProps / DropdownOption
 */

import React from 'react'
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from 'lucide-react'

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

export interface DropdownOption {
  label: string
  value: string
  disabled?: boolean
}

type Placement = 'top' | 'bottom' | 'left' | 'right'
type Size = 'xs' | 'sm' | 'md'

export interface DropdownProps {
  value: string
  onChange: (value: string) => void
  options: DropdownOption[]
  placement?: Placement
  size?: Size
  disabled?: boolean
  className?: string
}

// ---------------------------------------------------------------------------
// 常量
// ---------------------------------------------------------------------------

const PLACEMENT_CLASS: Record<Placement, string> = {
  top:    'dropdown-top',
  bottom: 'dropdown-bottom',
  left:   'dropdown-left',
  right:  'dropdown-right',
}

const PLACEMENT_ICON: Record<Placement, React.FC<{ size?: number | string; className?: string }>> = {
  top:    ChevronUp,
  bottom: ChevronDown,
  left:   ChevronLeft,
  right:  ChevronRight,
}

const TRIGGER_SIZE: Record<Size, string> = {
  xs: 'text-xs px-1.5 py-0',
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
}

const ICON_SIZE: Record<Size, number> = { xs: 10, sm: 12, md: 14 }

// ---------------------------------------------------------------------------
// 组件
// ---------------------------------------------------------------------------

export default function Dropdown({
  value,
  onChange,
  options,
  placement = 'bottom',
  size = 'sm',
  disabled = false,
  className = '',
}: DropdownProps) {
  const selected = options.find(o => o.value === value)
  const Icon = PLACEMENT_ICON[placement]

  return (
    <div className={`dropdown ${PLACEMENT_CLASS[placement]} dropdown-end ${disabled ? 'pointer-events-none opacity-50' : ''}`}>
      <button
        tabIndex={0}
        className={[
          'btn flex items-center gap-1',
          TRIGGER_SIZE[size],
          className,
        ].join(' ')}
        disabled={disabled}
      >
        {selected?.label ?? value}
        <Icon size={ICON_SIZE[size]} className="text-base-content/30" />
      </button>

      <ul
        tabIndex={0}
        className="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm"
      >
        {options.map(opt => (
          <li key={opt.value}>
            <a
              className={opt.value === value ? 'active' : ''}
              onClick={e => {
                e.preventDefault()
                if (opt.disabled) return
                onChange(opt.value)
                // 点击选项后手动移除焦点来关闭 dropdown
                ;(e.currentTarget.closest('.dropdown')?.querySelector('button') as HTMLElement)?.blur()
              }}
            >
              {opt.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
}
