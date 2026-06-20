/**
 * 创建时间: 2026-06-17
 * 作者: hongchuwudi
 * 描述: 通用选项框组件 — 统一替代原生 checkbox/toggle，与 FormSelect/FormInput 对等
 *
 * 包含:
 * - 组件: FormCheck — 复选框/开关，支持标签、必填、提示文字、错误态，自动适配 DaisyUI 样式
 */

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

type Size = 'xs' | 'sm' | 'md' | 'lg'
type CheckType = 'checkbox' | 'toggle'

export interface FormCheckProps {
  /** 字段名，用于原生 form 提交 */
  name?: string
  /** 选项框类型 */
  type?: CheckType
  /** 标签文字，不传则不渲染标签 */
  label?: string
  /** 尺寸 */
  size?: Size
  /** 是否选中 */
  checked: boolean
  /** 选中状态变化回调 */
  onChange: (checked: boolean) => void
  /** 是否禁用 */
  disabled?: boolean
  /** 外层 class */
  className?: string
  /** 是否必填 */
  required?: boolean
  /** 原生 title 属性（hover 提示） */
  title?: string
  /** 底部提示文字（校验提示、说明等） */
  hint?: string
  /** 是否处于错误态 */
  error?: boolean
}

// ---------------------------------------------------------------------------
// 工具
// ---------------------------------------------------------------------------

const CHECKBOX_SIZE_MAP: Record<Size, string> = {
  xs: 'checkbox-xs',
  sm: 'checkbox-sm',
  md: 'checkbox-md',
  lg: 'checkbox-lg',
}

const TOGGLE_SIZE_MAP: Record<Size, string> = {
  xs: 'toggle-xs',
  sm: 'toggle-sm',
  md: 'toggle-md',
  lg: 'toggle-lg',
}

// ---------------------------------------------------------------------------
// 组件
// ---------------------------------------------------------------------------

export default function FormCheck({
  name,
  type = 'checkbox',
  label,
  size = 'sm',
  checked,
  onChange,
  disabled = false,
  className = '',
  required = false,
  title,
  hint,
  error = false,
}: FormCheckProps) {
  const isToggle = type === 'toggle'
  const baseClass = isToggle ? 'toggle' : 'checkbox'
  const sizeClass = isToggle ? TOGGLE_SIZE_MAP[size] : CHECKBOX_SIZE_MAP[size]

  const inputClass = [
    baseClass,
    sizeClass,
    error && 'validator',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  const inputEl = (
    <input
      type="checkbox"
      name={name}
      checked={checked}
      onChange={e => onChange(e.target.checked)}
      disabled={disabled}
      required={required}
      title={title}
      className={inputClass}
    />
  )

  // hint 文字颜色跟随 error 状态
  const hintEl = hint && (
    <p className={`validator-hint ${error ? 'text-error' : 'text-base-content/40'}`}>
      {hint}
    </p>
  )

  // 无 label：只渲染控件 + hint
  if (!label) {
    return (
      <>
        {inputEl}
        {hintEl}
      </>
    )
  }

  // 有 label：flex 行内布局，与 FormInput checkbox/toggle 风格一致
  return (
    <div>
      <label className="flex items-center gap-1.5 cursor-pointer select-none text-xs text-base-content/60">
        {inputEl}
        <span>
          {label}
          {required && <span className="text-error ml-0.5">*</span>}
        </span>
      </label>
      {hintEl}
    </div>
  )
}
