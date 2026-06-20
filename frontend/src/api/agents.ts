/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: Agent 管理 API — 实时状态查询 + 提示词增删改查 + 决策历史
 *
 * 包含:
 * - fetchAgentStatus     — 获取所有 Agent 的当前运行状态
 * - fetchPrompts         — 获取所有 Agent 的提示词列表
 * - updatePrompt         — 更新单个 Agent 的提示词
 * - resetPrompt          — 重置单个 Agent 提示词为默认值
 * - reloadAgents         — 提示词变更后重新加载所有 Agent 实例
 * - fetchDecisions       — 分页查询 Agent 决策历史记录
 */

import { get, put, post } from '../utils/request'
import type { AgentStatusResponse, AgentPrompt, AgentDecisionPage } from '../types/agents'

// ── Agent 状态 ─────────────────────────────────────────

// 获取所有 Agent 的当前运行状态：调度师/分析师/复盘师/风控师/交易裁决员
// 返回各 Agent 的最新输入、输出、移交目标、时间戳
export const fetchAgentStatus = () => get<AgentStatusResponse>('/agents/status')

// ── 提示词管理 ────────────────────────────────────────

// 获取所有 Agent 的提示词列表，包含名称、版本号、内容文本
export const fetchPrompts = () => get<AgentPrompt[]>('/agents/prompts')

// 更新单个 Agent 的提示词文本，name 为提示词文件名（不含扩展名）
// 保存后版本号自动递增，需调用 reloadAgents 使变更生效
export const updatePrompt = (name: string, text: string) =>
  put<{ ok: boolean }>(`/agents/prompts/${name}`, { text })

// 重置单个 Agent 的提示词为系统默认值（从代码模板恢复）
export const resetPrompt = (name: string) =>
  post<{ ok: boolean }>(`/agents/prompts/${name}/reset`)

// 提示词变更后重新加载所有 Agent 实例，使新提示词立即生效
// 注意：运行中的 tick 不受影响，下一个 tick 开始使用新提示词
export const reloadAgents = () =>
  post<{ ok: boolean; message: string }>('/agents/reload')

// ── 决策历史 ──────────────────────────────────────────

// 分页查询 Agent 决策历史记录，每 tick 存一条
// 返回 { data, page, page_size, total, total_pages }
// 每条记录含 signal/confidence/reason/stop_loss/take_profit/mode
export const fetchDecisions = (page = 1, pageSize = 20) =>
  get<AgentDecisionPage>(`/agents/decisions?page=${page}&page_size=${pageSize}`)
