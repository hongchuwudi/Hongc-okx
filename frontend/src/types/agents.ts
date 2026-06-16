/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: Agent 状态模块类型
 */

// Agent 单条事件
export interface AgentEvent {
  type: 'agent_input' | 'agent_output' | 'agent_tool_call'
  agent: string
  ts: string
  input?: string
  output?: string
  handoff?: string
  tool?: string
  args?: string
  result?: string
}

// GET /api/v1/agents/status
export interface AgentStatusResponse {
  agents: Record<string, { latest: AgentEvent }>
  history: AgentEvent[]
  tick_count: number
}

// GET /api/v1/agents/prompts
export interface AgentPrompt {
  name: string
  label: string
  text: string
  default: string
  modified: boolean
}

// GET /api/v1/agents/decisions
export interface AgentDecision {
  id: number
  timestamp: string
  mode: string
  agents_json: string
  signal: string
  confidence: string
  reason: string
  stop_loss: number
  take_profit: number
  source_count: number
}

export interface AgentDecisionPage {
  data: AgentDecision[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

// Agent 运行时状态（日志管道可视化用）
export interface AgentRunState {
  hasInput: boolean
  hasOutput: boolean
  toolCount: number
  lastTs: string | null
}
