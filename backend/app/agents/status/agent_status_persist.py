"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: agent_status_persist.py Agent 决策持久化
描述: 将每个 tick 的 Agent 输出持久化到 PostgreSQL + Redis 缓存

包含:
- 函数: save_tick_agent_logs — 持久化当前 tick 的全部 Agent 决策
"""

import json
import re
from datetime import datetime

from app.core.logger import get_logger
from app.harness.emoji_clean import strip_emoji

logger = get_logger()


async def save_tick_agent_logs(mode: str, signal: str = "HOLD", confidence: str = "LOW",
                                reason: str = "", stop_loss: float = 0, take_profit: float = 0,
                                source_count: int = 0) -> None:
    """当前 tick 完成后，将所有 Agent 的 output 持久化到 DB + Redis 缓存。"""
    from app.agents.status.agent_status_publish import _latest, _get_redis

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
        await redis.ltrim(key, 0, 9)
    except Exception:
        pass

    # 2. 写 PostgreSQL 持久化（入库前清洗 emoji，防止前端显示异常）
    try:
        from app.core.database import get_sync_session
        from app.entities.agent_decision import AgentDecision
        sess = get_sync_session()
        row = AgentDecision(
            timestamp=ts, mode=mode, agents_json=agents_text,
            signal=strip_emoji(signal),
            confidence=strip_emoji(confidence),
            reason=strip_emoji(reason),
            stop_loss=stop_loss, take_profit=take_profit, source_count=source_count,
        )
        sess.add(row)
        sess.commit()
        sess.close()
    except Exception as e:
        logger.error(f"Agent 决策入库失败: {type(e).__name__}: {e}")
