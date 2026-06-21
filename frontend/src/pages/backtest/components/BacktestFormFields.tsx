/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测表单字段 — 统一使用 FormSelect / FormInput，menu 风格
 *
 * 包含:
 * - 组件: SelectField / TextField / NumberField — 回测参数输入
 */

import FormSelect from '@/components/common/FormSelect'
import FormInput from '@/components/common/FormInput'
import type { BacktestRunRequest } from '@/types/backtest'

interface FieldProps {
  label: string
  field: keyof BacktestRunRequest
  onChange: (k: keyof BacktestRunRequest, v: string | number) => void
}

interface SelectFieldProps extends FieldProps {
  value: string
  options: { label: string; value: string }[]
}

interface InputFieldProps extends FieldProps {
  value: string
}

interface NumberFieldProps extends FieldProps {
  value: number
  step?: number
}

export function SelectField({ label, field, value, options, onChange }: SelectFieldProps) {
  return (
    <FormSelect
      label={label}
      size="sm"
      value={value}
      options={options}
      onChange={v => onChange(field, v)}
      className="w-full"
    />
  )
}

export function TextField({ label, field, value, onChange }: InputFieldProps) {
  return (
    <FormInput
      label={label}
      size="sm"
      value={value}
      onChange={v => onChange(field, v)}
      className="w-full"
    />
  )
}

export function NumberField({ label, field, value, onChange, step = 1 }: NumberFieldProps) {
  return (
    <FormInput
      label={label}
      type="number"
      size="sm"
      value={String(value)}
      step={step}
      onChange={v => onChange(field, parseFloat(v) || 0)}
      className="w-full"
    />
  )
}
