/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 通用输入框组件 — daisyUI 5 label.input 模式，统一替代原生 input
 *
 * 包含:
 * - 组件: FormInput — 文本/数字/密码/邮箱/复选框/开关
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

const INPUT_SIZE: Record<Size, string> = {
  xs: 'input-xs',
  sm: 'input-sm',
  md: 'input-md',
  lg: 'input-lg',
}

const CHECK_SIZE: Record<Size, string> = {
  xs: 'checkbox-xs',
  sm: 'checkbox-sm',
  md: 'checkbox-md',
  lg: 'checkbox-lg',
}

const TOGGLE_SIZE: Record<Size, string> = {
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
    const base = isToggle ? 'toggle' : 'checkbox'
    const sz = isToggle ? TOGGLE_SIZE[size] : CHECK_SIZE[size]

    const el = (
      <input
        type="checkbox"
        checked={props.checked}
        onChange={e => props.onChange(e.target.checked)}
        disabled={disabled}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
        className={`${base} ${sz} ${className}`.trim()}
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
  const { type = 'text', value, onChange, placeholder, step, min, max } = props

  // daisyUI 5 模式: label 作为容器，类名加在 label 上
  if (label) {
    return (
      <label className={`input ${INPUT_SIZE[size]} ${disabled ? 'input-disabled' : ''} shadow-sm flex items-center gap-2 ${className}`.trim()}>
        <span className="label text-xs text-base-content/50 shrink-0">{label}</span>
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
          className="grow bg-transparent outline-none text-sm placeholder:text-base-content/20"
        />
      </label>
    )
  }

  // 无标签：input 类直接加在 input 上
  return (
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
      className={`input ${INPUT_SIZE[size]} shadow-sm ${className}`.trim()}
    />
  )
}
