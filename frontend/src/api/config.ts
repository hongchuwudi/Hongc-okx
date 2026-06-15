/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 系统配置 API — 动态配置的读取、修改、重置
 *       运行时配置通过 Redis 实时生效，持久化配置存 PostgreSQL
 */

import { get, put, post, del } from '../utils/request'
import type { ConfigData, ConfigUpdate } from '../types/config'

// ── 持久化配置（PG）───────────────────────────────────

// 获取当前系统配置：杠杆、下单金额、仓位上限、tick 间隔、风控阈值等
// 配置持久化在 PostgreSQL，重启不丢失
export const fetchConfig = () => get<ConfigData>('/config')

// 部分更新系统配置：只传需要修改的字段即可，未传字段保持原值
// 可更新：leverage/order_amount/max_position_ratio/tick_interval_seconds/风控参数
export const updateConfig = (body: ConfigUpdate) => put<ConfigData>('/config', body)

// 重置所有配置为代码默认值（config_trade.py 中的原始值）
export const resetConfig = () => post<ConfigData>('/config/reset')

// ── 运行时配置（Redis，即时生效）─────────────────────

// 获取 Redis 运行时配置（实时生效的值，Redis 优先 + env fallback）
export const fetchRuntimeConfig = () => get<ConfigData>('/config/runtime')

// 直接写入 Redis 运行时配置（不持久化到 PG，重启后恢复 env 默认值）
export const updateRuntimeConfig = (body: ConfigUpdate) => put<{ ok: boolean; updated: string[] }>('/config/runtime', body)

// 删除单个运行时配置 key，恢复 env 默认值
export const deleteRuntimeConfig = (key: string) => del<{ ok: boolean; deleted: string }>(`/config/runtime/${key}`)
