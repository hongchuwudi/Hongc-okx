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

from app.core.logger import get_logger

logger = get_logger()
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


# 推送 Agent 状态事件到 Redis Pub/Sub + 存入内存供 API 查询。
async def publish_agent_status(event_type: str, agent_name: str, **kwargs):
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
        data = json.dumps(payload, ensure_ascii=False, default=str)
        count = await redis.publish("ws:channel:updates", data)
        from app.core.logger import get_logger
        get_logger().info(f"[agent_status] 发布 {event_type}/{agent_name} → 订阅者数={count}")
    except Exception as e:
        from app.core.logger import get_logger
        get_logger().warning(f"[agent_status] 发布失败: {e}")


# Agent 开始运行：推送收到的输入摘要。
async def agent_input(agent_name: str, summary: str):
    await publish_agent_status("agent_input", agent_name, input=summary)


# Agent 完成运行：推送输出摘要和移交目标。
async def agent_output(agent_name: str, summary: str, handoff: str | None = None):
    await publish_agent_status("agent_output", agent_name,
                               output=summary,
                               handoff=handoff or "none")


# Agent 调用了工具：推送工具名、入参、返回值。
async def agent_tool_call(agent_name: str, tool_name: str, args: str, result: str):
    await publish_agent_status("agent_tool_call", agent_name,
                               tool=tool_name, args=args, result=result)


# 当前 tick 完成后，将所有 Agent 的 output 持久化到 DB + Redis 缓存。
async def save_tick_agent_logs(mode: str, signal: str = "HOLD", confidence: str = "LOW",
                                reason: str = "", stop_loss: float = 0, take_profit: float = 0,
                                source_count: int = 0) -> None:
    ts = datetime.utcnow()
    agents_dict = {
        name: {"output": data.get("output", ""), "handoff": data.get("handoff", "none")}
        for name, data in _latest.items()
        if data.get("type") == "agent_output"
    }
    agents_text = json.dumps(agents_dict, ensure_ascii=False, default=str)

    # 1. 写 Redis 缓存（最近 10 条）
    redis_payload = {"ts": ts.isoformat(), "mode": mode, "agents": agents_dict}
    try:
        redis = await _get_redis()
        key = "agent:logs:recent"
        await redis.lpush(key, json.dumps(redis_payload, ensure_ascii=False, default=str))
        await redis.ltrim(key, 0, 9)  # 保留最近 10 条
    except Exception:
        pass

    # 2. 写 PostgreSQL 持久化
    try:
        from app.database import get_sync_session
        from app.entities.agent_decision import AgentDecision
        sess = get_sync_session()
        row = AgentDecision(
            timestamp=ts, mode=mode, agents_json=agents_text,
            signal=signal, confidence=confidence, reason=reason,
            stop_loss=stop_loss, take_profit=take_profit, source_count=source_count,
        )
        sess.add(row)
        sess.commit()
        sess.close()
    except Exception as e:
        logger.error(f"Agent 决策入库失败: {type(e).__name__}: {e}")


# 分页查询 Agent 决策历史记录。
def query_agent_decisions(page: int = 1, page_size: int = 20) -> dict:
    from app.database import get_sync_session
    from app.entities.agent_decision import AgentDecision
    sess = get_sync_session()
    try:
        total = sess.query(AgentDecision).count()
        offset = (page - 1) * page_size
        rows = (
            sess.query(AgentDecision)
            .order_by(AgentDecision.timestamp.desc())
            .offset(offset).limit(page_size).all()
        )
        data = [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                "mode": r.mode,
                "agents_json": r.agents_json,
                "signal": r.signal,
                "confidence": r.confidence,
                "reason": r.reason,
                "stop_loss": r.stop_loss,
                "take_profit": r.take_profit,
                "source_count": r.source_count,
            }
            for r in rows
        ]
        return {
            "data": data, "page": page, "page_size": page_size,
            "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }
    finally:
        sess.close()


# 查询最近 N 轮的 Agent 输出快照（Redis 缓存）。
async def get_recent_agent_logs(limit: int = 5) -> list[dict]:
    """从 Redis 读取最近 N 条 agent 日志。"""
    try:
        redis = await _get_redis()
        raw = await redis.lrange("agent:logs:recent", 0, limit - 1)
        return [json.loads(r) for r in raw]
    except Exception:
        return []


# 分页查询 Agent 日志。
async def get_agent_logs_paginated(page: int = 1, page_size: int = 20) -> dict:
    """从 Redis 分页读取 agent 日志。"""
    try:
        redis = await _get_redis()
        key = "agent:logs:recent"
        total = await redis.llen(key)
        start = (page - 1) * page_size
        end = start + page_size - 1
        raw = await redis.lrange(key, start, end)
        items = [json.loads(r) for r in raw]
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    except Exception:
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}


# API 查询：返回每个 Agent 的最新状态 + 最近 50 条历史记录。
def get_agents_status() -> dict:
    return {
        "agents": {
            name: {"latest": status}
            for name, status in _latest.items()
        },
        "history": list(_history)[-50:],  # 最近 50 条
        "tick_count": len([e for e in _history if e["type"] == "agent_output"]),
    }
