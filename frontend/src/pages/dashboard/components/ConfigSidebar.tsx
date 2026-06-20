/**
 * Created: 2026-06-14
 * Author: hongchuwudi
 * Description: 运行时配置侧边栏 — 展示/修改交易参数和风控参数，即时生效
 *
 * Contains:
 * - Component: ConfigSidebar — 左侧配置面板，区分交易参数/风控参数两个分组
 * - Component: ConfigField — 单个配置字段
 */

import { useState, useEffect, useCallback } from 'react'
import { fetchRuntimeConfig, updateRuntimeConfig } from '@/api/config'
import { CONFIG_FIELDS } from '@/constants/config'
import type { ConfigData, ConfigFieldMeta } from '@/types/config'
import FormInput from '@/components/common/FormInput'
import FormSelect from '@/components/common/FormSelect'

export default function ConfigSidebar({ onConfigChange }: { onConfigChange?: () => void }) {
  const [config, setConfig] = useState<ConfigData | null>(null)
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState('')

  // 加载运行时配置
  const load = useCallback(async () => {
    try {
      const data = await fetchRuntimeConfig()
      setConfig(data)
      setError('')
    } catch {
      setError('加载配置失败')
    }
  }, [])

  useEffect(() => { load() }, [load])

  // 更新单个字段
  const handleChange = useCallback(async (key: string, value: string | number) => {
    if (!config) return
    const field = CONFIG_FIELDS.find(f => f.key === key)
    const newVal = field?.type === 'number' ? Number(value) : String(value)

    // 乐观更新
    setConfig(prev => prev ? { ...prev, [key]: newVal } : prev)
    setSaving(key)
    try {
      await updateRuntimeConfig({ [key]: newVal })
      setError('')
      onConfigChange?.()  // 通知父组件配置已变更
    } catch {
      setError(`保存 ${field?.label || key} 失败`)
      // 回滚
      setConfig(prev => prev ? { ...prev, [key]: config[key as keyof ConfigData] } : prev)
    } finally {
      setSaving(null)
    }
  }, [config, onConfigChange])

  if (!config) {
    return (
      <div className="card bg-base-100 border border-base-300 h-full">
        <div className="card-body p-4 flex items-center justify-center">
          {error ? (
            <div className="text-error text-sm text-center">
              <p>{error}</p>
              <button onClick={load} className="btn btn-ghost btn-xs mt-1">重试</button>
            </div>
          ) : (
            <span className="loading loading-spinner loading-sm" />
          )}
        </div>
      </div>
    )
  }

  // 分组: 交易参数 / 风控参数
  const tradeFields = CONFIG_FIELDS.filter(f => ['agent_mode', 'symbol', 'timeframe', 'tick_interval_seconds', 'leverage', 'order_amount'].includes(f.key))
  const riskFields = CONFIG_FIELDS.filter(f => ['max_position_ratio', 'max_daily_drawdown_pct', 'max_daily_loss_usdt'].includes(f.key))

  return (
    <div className="card bg-base-100 border border-base-300 h-full rounded-none">
      <div className="card-body p-3 space-y-3 overflow-y-auto">
        <h2 className="card-title text-sm">运行配置</h2>

        {error && <div className="text-error text-xs">{error}</div>}

        {/* 交易参数 */}
        <div>
          <p className="text-xs text-base-content/40 mb-2">交易参数</p>
          <div className="space-y-2">
            {tradeFields.map(field => (
              <ConfigField
                key={field.key}
                field={field}
                value={config[field.key as keyof ConfigData]}
                saving={saving === field.key}
                onChange={handleChange}
              />
            ))}
          </div>
        </div>

        <div className="divider my-0" />

        {/* 风控参数 */}
        <div>
          <p className="text-xs text-base-content/40 mb-2">风控参数</p>
          <div className="space-y-2">
            {riskFields.map(field => (
              <ConfigField
                key={field.key}
                field={field}
                value={config[field.key as keyof ConfigData]}
                saving={saving === field.key}
                onChange={handleChange}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── 单个字段 ──────────────────────────────────────────

function ConfigField({
  field,
  value,
  saving,
  onChange,
}: {
  field: ConfigFieldMeta
  value: string | number | boolean
  saving: boolean
  onChange: (key: string, value: string | number) => void
}) {
  const [local, setLocal] = useState(value)
  // 外部值变化时同步（如保存失败回滚）
  useEffect(() => { setLocal(value) }, [value])

  return (
    <label className="form-control w-full">
      <div className="flex items-center justify-between mb-0.5">
        <span className="label-text text-xs text-base-content/60">{field.label}</span>
        <span className={`badge badge-xs ${field.instant ? 'badge-success' : 'badge-ghost'} text-[10px]`}>
          {field.instant ? '即时' : '重启'}
        </span>
      </div>
      <div className="relative">
        {field.type === 'select' && field.options ? (
          <FormSelect
            size="xs"
            value={String(local)}
            options={field.options}
            onChange={v => { setLocal(v); onChange(field.key, v) }}
            disabled={saving}
            className="w-full"
          />
        ) : (
          <FormInput
            type="number"
            size="xs"
            value={String(local)}
            step={field.step}
            min={field.min}
            max={field.max}
            onChange={v => setLocal(Number(v))}
            onBlur={() => onChange(field.key, local as number)}
            onKeyDown={e => { if (e.key === 'Enter') onChange(field.key, local as number) }}
            disabled={saving}
            className="w-full"
          />
        )}
        {saving && (
          <span className="loading loading-spinner loading-xs absolute right-2 top-1/2 -translate-y-1/2" />
        )}
      </div>
    </label>
  )
}
