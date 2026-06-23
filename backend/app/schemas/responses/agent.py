"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: Agent 状态响应 VO — GET /api/agents/status

包含:
- 类: AgentEvent / AgentInfo / AgentStatusResponse — Agent 实时状态
- 类: DeepSeekBalanceResponse — DeepSeek 账户余额响应
"""

from typing import Optional
from pydantic import BaseModel


class AgentEvent(BaseModel):
    type: str
    agent: str
    ts: str
    input: Optional[str] = None
    output: Optional[str] = None
    handoff: Optional[str] = None
    tool: Optional[str] = None
    args: Optional[str] = None
    result: Optional[str] = None


class AgentInfo(BaseModel):
    latest: AgentEvent


class AgentStatusResponse(BaseModel):
    agents: dict[str, AgentInfo]
    history: list[AgentEvent]
    tick_count: int


class DeepSeekBalanceResponse(BaseModel):
    """GET /api/v1/config/ai-balance 响应 — DeepSeek 账户余额"""
    is_available: bool                # 账户是否可用
    total_balance: float              # 总余额（CNY）
    currency: str = "CNY"             # 币种
    granted_balance: float = 0.0      # 赠送余额
    topped_up_balance: float = 0.0    # 充值余额
    degrade_threshold: float          # 降级阈值（低于此值走技术指标）
    degraded: bool                    # 当前是否处于降级区间（余额 < 阈值）
