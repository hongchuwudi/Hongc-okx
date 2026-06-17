"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: agent_status_publish.py Agent 状态发布核心
描述: 共享状态管理 + Redis Pub/Sub 推送通道

包含:
- 变量: _latest — 每个 Agent 的最新状态快照
- 变量: _history — 全局事件历史（deque 最多 200 条）
- 函数: _get_redis — 惰性获取 Redis Pub/Sub 连接
- 函数: publish_agent_status — 推送 Agent 状态事件到 Redis + 存入内存
"""

import json
from datetime import datetime
from collections import deque

from app.core.logger import get_logger

logger = get_logger()
_redis = None

# 每个 Agent 的最新状态: {"scheduler": {"input": "...", "output": "...", "handoff": "analyst", "ts": "..."}}
_latest: dict[str, dict] = {}
# 每个事件类型的历史: deque 最多保留 200 条
_history: deque = deque(maxlen=200)


async def _get_redis():
    """惰性获取 Redis Pub/Sub 连接。"""
    global _redis
    if _redis is None:
        from app.core.database import get_redis_pubsub
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
        data = json.dumps(payload, ensure_ascii=False, default=str)
        count = await redis.publish("ws:channel:updates", data)
        logger.info(f"[agent_status] 发布 {event_type}/{agent_name} -> 订阅者数={count}")
    except Exception as e:
        logger.warning(f"[agent_status] 发布失败: {e}")
