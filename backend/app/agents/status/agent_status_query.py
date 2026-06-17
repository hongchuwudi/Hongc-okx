"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: agent_status_query.py Agent 状态查询
描述: 从 PostgreSQL / Redis / 内存查询 Agent 状态和决策历史

包含:
- 函数: query_agent_decisions — PG 分页查询 Agent 决策历史
- 函数: get_recent_agent_logs — Redis 查询最近 N 轮 Agent 输出快照
- 函数: get_agent_logs_paginated — Redis 分页查询 Agent 日志
- 函数: get_agents_status — 内存查询：各 Agent 最新状态 + 最近 50 条历史
"""

import json


def query_agent_decisions(page: int = 1, page_size: int = 20) -> dict:
    """分页查询 Agent 决策历史记录（PostgreSQL）。"""
    from app.core.database import get_sync_session
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


async def get_recent_agent_logs(limit: int = 5) -> list[dict]:
    """从 Redis 读取最近 N 条 agent 日志。"""
    try:
        from app.agents.status.agent_status_publish import _get_redis
        redis = await _get_redis()
        raw = await redis.lrange("agent:logs:recent", 0, limit - 1)
        return [json.loads(r) for r in raw]
    except Exception:
        return []


async def get_agent_logs_paginated(page: int = 1, page_size: int = 20) -> dict:
    """从 Redis 分页读取 agent 日志。"""
    try:
        from app.agents.status.agent_status_publish import _get_redis
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


def get_agents_status() -> dict:
    """API 查询：返回每个 Agent 的最新状态 + 最近 50 条历史记录。"""
    from app.agents.status.agent_status_publish import _latest, _history
    return {
        "agents": {
            name: {"latest": status}
            for name, status in _latest.items()
        },
        "history": list(_history)[-50:],
        "tick_count": len([e for e in _history if e["type"] == "agent_output"]),
    }
