"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: agent_status.py Agent状态总线
描述: 每个 Agent 的输入/输出/状态暴露给前端 — 通过 Redis Pub/Sub 实时推送

包含:
- 函数: publish_agent_status — 推送 Agent 状态到 WebSocket
- 函数: agent_input — 标记 Agent 开始运行（记录输入）
- 函数: agent_output — 标记 Agent 完成（记录输出）
- 常量: _redis — Redis 连接缓存
"""

import json
import asyncio
from datetime import datetime
from collections import defaultdict, deque

_redis = None

# 每个 Agent 的最新状态: {"scheduler": {"input": "...", "output": "...", "handoff": "analyst", "ts": "..."}}
_latest: dict[str, dict] = {}
# 每个事件类型的历史: deque 最多保留 200 条
_history: deque = deque(maxlen=200)


async def _get_redis():
    global _redis
    if _redis is None:
        from app.database import get_redis_pubsub
        _redis = await get_redis_pubsub()
    return _redis


async def publish_agent_status(event_type: str, agent_name: str, **kwargs):
    """推送 Agent 状态事件到 Redis Pub/Sub + 存入内存供 API 查询。"""
    payload = {
        "type": event_type,
        "agent": agent_name,
        "ts": datetime.utcnow().isoformat(),
        **kwargs,
    }
    # 更新最新状态
    _latest[agent_name] = payload
    # 追加历史
    _history.append(payload)
    # 推送 WebSocket
    try:
        redis = await _get_redis()
        await redis.publish("ws:channel:updates", json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        pass


async def agent_input(agent_name: str, summary: str):
    """Agent 开始运行：推送收到的输入摘要。"""
    await publish_agent_status("agent_input", agent_name, input=summary)


async def agent_output(agent_name: str, summary: str, handoff: str | None = None):
    """Agent 完成运行：推送输出摘要和移交目标。"""
    await publish_agent_status("agent_output", agent_name,
                               output=summary,
                               handoff=handoff or "none")


async def agent_tool_call(agent_name: str, tool_name: str, args: str, result: str):
    """Agent 调用了工具：推送工具名、入参、返回值。"""
    await publish_agent_status("agent_tool_call", agent_name,
                               tool=tool_name, args=args, result=result)


def get_agents_status() -> dict:
    """API 查询：返回每个 Agent 的最新状态 + 最近 50 条历史记录。"""
    return {
        "agents": {
            name: {"latest": status}
            for name, status in _latest.items()
        },
        "history": list(_history)[-50:],  # 最近 50 条
        "tick_count": len([e for e in _history if e["type"] == "agent_output"]),
    }
