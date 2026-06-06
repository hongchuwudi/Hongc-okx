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

_redis = None


async def _get_redis():
    global _redis
    if _redis is None:
        from app.database import get_redis_pubsub
        _redis = await get_redis_pubsub()
    return _redis


async def publish_agent_status(event_type: str, agent_name: str, **kwargs):
    """推送 Agent 状态事件到 Redis Pub/Sub，前端通过 WebSocket 接收。"""
    try:
        redis = await _get_redis()
        payload = {
            "type": event_type,
            "agent": agent_name,
            "ts": datetime.utcnow().isoformat(),
            **kwargs,
        }
        await redis.publish("ws:channel:updates", json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        pass  # Redis 不可用不影响交易


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
