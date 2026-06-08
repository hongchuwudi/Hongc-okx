"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: Agent 状态响应 VO — GET /api/agents/status
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
