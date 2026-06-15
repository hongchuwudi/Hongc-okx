/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 通用下拉框组件 — 统一替代原生 select，与 FormInput 对等
 *
 * 包含:
 * - 组件: FormSelect — 通用下拉框，自动适配 DaisyUI 样式
 */

import React from 'react'

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

type Size = 'xs' | 'sm' | 'md' | 'lg'

interface FormSelectOption {
  label: string
  value: string
}

export interface FormSelectProps {
  label?: string
  size?: Size
  value: string
  onChange: (value: string) => void
  options: FormSelectOption[]
  disabled?: boolean
  className?: string
  placeholder?: string
}

// ---------------------------------------------------------------------------
// 工具
// ---------------------------------------------------------------------------

const SIZE_MAP: Record<Size, string> = {
  xs: 'select-xs',
  sm: 'select-sm',
  md: 'select-md',
  lg: 'select-lg',
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
}: FormSelectProps) {
  const selectEl = (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      disabled={disabled}
      className={`select ${SIZE_MAP[size]} ${className}`.trim()}
    >
      {placeholder && (
        <option value="" disabled>{placeholder}</option>
      )}
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  )

  if (label) {
    return (
      <label className="form-control">
        <span className="label-text text-xs text-base-content/60 mb-1">{label}</span>
        {selectEl}
      </label>
    )
  }

  return selectEl
}
