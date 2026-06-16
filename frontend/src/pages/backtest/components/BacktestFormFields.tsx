/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测表单字段 — 下拉/文本/数字三种输入
 */

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

// 下拉选择
export function SelectField({ label, field, value, options, onChange }: SelectFieldProps) {
  return (
    <label className="form-control">
      <span className="label-text text-xs text-base-content/60 mb-1">{label}</span>
      <select
        value={value}
        onChange={e => onChange(field, e.target.value)}
        className="select select-sm select-bordered"
      >
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  )
}

// 文本输入
export function TextField({ label, field, value, onChange }: InputFieldProps) {
  return (
    <label className="form-control">
      <span className="label-text text-xs text-base-content/60 mb-1">{label}</span>
      <input
        value={value}
        onChange={e => onChange(field, e.target.value)}
        className="input input-sm input-bordered"
      />
    </label>
  )
}

// 数字输入
export function NumberField({ label, field, value, onChange, step = 1 }: NumberFieldProps) {
  return (
    <label className="form-control">
      <span className="label-text text-xs text-base-content/60 mb-1">{label}</span>
      <input
        type="number" step={step} value={value}
        onChange={e => onChange(field, parseFloat(e.target.value) || 0)}
        className="input input-sm input-bordered"
      />
    </label>
  )
}
