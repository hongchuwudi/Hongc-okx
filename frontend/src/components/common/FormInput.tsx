/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 通用输入框组件 — 统一替代原生 input，支持文本/数字/密码/邮箱/复选框/开关
 *
 * 包含:
 * - 组件: FormInput — 通用输入框，自动适配 DaisyUI 样式
 */

import React from 'react'

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

type Size = 'xs' | 'sm' | 'md' | 'lg'

interface BaseProps {
  label?: string
  size?: Size
  disabled?: boolean
  className?: string
  onBlur?: () => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void
}

interface TextInputProps extends BaseProps {
  type?: 'text' | 'number' | 'password' | 'email'
  value: string
  onChange: (value: string) => void
  placeholder?: string
  step?: number
  min?: number
  max?: number
}

interface CheckInputProps extends BaseProps {
  type: 'checkbox' | 'toggle'
  checked: boolean
  onChange: (checked: boolean) => void
}

export type FormInputProps = TextInputProps | CheckInputProps

// ---------------------------------------------------------------------------
// 工具
// ---------------------------------------------------------------------------

const SIZE_MAP: Record<Size, string> = {
  xs: 'input-xs',
  sm: 'input-sm',
  md: 'input-md',
  lg: 'input-lg',
}

const CHECK_SIZE_MAP: Record<Size, string> = {
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

export default function FormInput(props: FormInputProps) {
  const { label, size = 'sm', disabled = false, className = '', onBlur, onKeyDown } = props

  // ── 复选框 / 开关 ──────────────────────────────────
  if ('checked' in props) {
    const isToggle = props.type === 'toggle'
    const baseClass = isToggle ? 'toggle' : 'checkbox'
    const sizeClass = isToggle ? TOGGLE_SIZE_MAP[size] : CHECK_SIZE_MAP[size]

    const el = (
      <input
        type="checkbox"
        checked={props.checked}
        onChange={e => props.onChange(e.target.checked)}
        disabled={disabled}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
        className={`${baseClass} ${sizeClass} ${className}`.trim()}
      />
    )

    if (label) {
      return (
        <label className="flex items-center gap-1.5 cursor-pointer select-none text-xs text-base-content/60">
          {el}
          <span>{label}</span>
        </label>
      )
    }
    return el
  }

  // ── 文本 / 数字 / 密码 / 邮箱 ──────────────────────
  const {
    type = 'text',
    value,
    onChange,
    placeholder,
    step,
    min,
    max,
  } = props

  const inputEl = (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      step={step}
      min={min}
      max={max}
      onBlur={onBlur}
      onKeyDown={onKeyDown}
      className={`input ${SIZE_MAP[size]} ${className}`.trim()}
    />
  )

  if (label) {
    return (
      <label className="form-control">
        <span className="label-text text-xs text-base-content/60 mb-1">{label}</span>
        {inputEl}
      </label>
    )
  }

  return inputEl
}
