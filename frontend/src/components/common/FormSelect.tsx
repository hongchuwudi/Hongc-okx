/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 通用下拉选择组件 — daisyUI dropdown 模式
 *
 * 包含:
 * - 组件: FormSelect — 点击弹出选项菜单
 * - 类型: FormSelectProps / FormSelectOption
 */

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

type Size = 'xs' | 'sm' | 'md' | 'lg'

export interface FormSelectOption {
  label: string
  value: string
  disabled?: boolean
}

export interface FormSelectProps {
  name?: string
  label?: string
  size?: Size
  value: string
  onChange: (value: string) => void
  options: FormSelectOption[]
  disabled?: boolean
  className?: string
  placeholder?: string
  required?: boolean
  hint?: string
  error?: boolean
}

// ---------------------------------------------------------------------------
// 常量
// ---------------------------------------------------------------------------

const TRIGGER_SIZE: Record<Size, string> = {
  xs: 'btn-xs',
  sm: 'btn-sm',
  md: 'btn-md',
  lg: 'btn-lg',
}

// ---------------------------------------------------------------------------
// 组件
// ---------------------------------------------------------------------------

export default function FormSelect({
  label,
  size = 'sm',
  value,
  onChange,
  options,
  disabled = false,
  className = '',
  placeholder,
  required = false,
  hint,
  error = false,
}: FormSelectProps) {
  const selected = options.find(o => o.value === value)

  const hintEl = hint && (
    <span className={`text-xs ${error ? 'text-error' : 'text-base-content/40'}`}>
      {hint}
    </span>
  )

  const dropdown = (
    <div className={`dropdown dropdown-bottom dropdown-end ${label ? 'min-w-0 flex-1' : className}`}>
      <div tabIndex={0} role="button" className={`btn ${TRIGGER_SIZE[size]} ${error ? 'btn-error' : ''} ${disabled ? 'btn-disabled' : ''} w-full`}>
        {selected?.label ?? placeholder ?? value}
      </div>
      <ul tabIndex={0} className="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm">
        {options.map(opt => (
          <li key={opt.value}>
            <a
              className={opt.value === value ? 'active' : ''}
              onClick={e => {
                e.preventDefault()
                if (opt.disabled) return
                onChange(opt.value)
                ;(e.currentTarget.closest('.dropdown')?.querySelector('[tabindex]') as HTMLElement)?.blur()
              }}
            >
              {opt.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  )

  if (label) {
    return (
      <div>
        <label className="flex items-center gap-2">
          <span className="text-xs text-base-content/50 shrink-0">
            {label}
            {required && <span className="text-error ml-0.5">*</span>}
          </span>
          {dropdown}
        </label>
        {hintEl}
      </div>
    )
  }

  return (
    <>
      {dropdown}
      {hintEl}
    </>
  )
}
