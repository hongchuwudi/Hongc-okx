"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: agents.py Agent状态API
描述: Agent 状态查询接口 — GET /api/agents/status

包含:
- 端点: get_agents_status — 返回 5 个 Agent 的最新状态和历史记录
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/status")
def get_agents_status():
    """返回每个 Agent 的最新状态 + 最近 50 条事件历史。"""
    from app.agents.agent_status import get_agents_status as _get
    return _get()
