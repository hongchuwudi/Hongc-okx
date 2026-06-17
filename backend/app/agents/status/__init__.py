"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: agent_status/ Agent 状态总线
描述: 每个 Agent 的输入/输出/状态暴露给前端 — 通过 Redis Pub/Sub 实时推送

目录结构:
- agent_status_publish.py — _get_redis(), _latest, _history, publish_agent_status()
- agent_status_hooks.py   — agent_input(), agent_output(), agent_tool_call()
- agent_status_persist.py — _strip_emoji(), save_tick_agent_logs()
- agent_status_query.py   — query_agent_decisions(), get_recent_agent_logs(),
                              get_agent_logs_paginated(), get_agents_status()

包含:
- 所有公开函数从子模块重导出，向后兼容
"""

from app.agents.status.agent_status_publish import publish_agent_status
from app.agents.status.agent_status_hooks import agent_input, agent_output, agent_tool_call
from app.agents.status.agent_status_persist import save_tick_agent_logs
from app.agents.status.agent_status_query import (
    query_agent_decisions,
    get_recent_agent_logs,
    get_agent_logs_paginated,
    get_agents_status,
)
