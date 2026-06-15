/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: Agent 状态 API — Agent 实时状态 + 提示词管理
 */

import { get, put, post } from '../utils/request'
import type { AgentStatusResponse, AgentPrompt, AgentDecisionPage } from '../types/agents'

// Agent 状态
export const fetchAgentStatus = () => get<AgentStatusResponse>('/agents/status')

// 提示词管理
export const fetchPrompts = () => get<AgentPrompt[]>('/agents/prompts')

export const updatePrompt = (name: string, text: string) =>
  put<{ ok: boolean }>(`/agents/prompts/${name}`, { text })

export const resetPrompt = (name: string) =>
  post<{ ok: boolean }>(`/agents/prompts/${name}/reset`)

export const reloadAgents = () =>
  post<{ ok: boolean; message: string }>('/agents/reload')

export const fetchDecisions = (page = 1, pageSize = 20) =>
  get<AgentDecisionPage>(`/agents/decisions?page=${page}&page_size=${pageSize}`)
