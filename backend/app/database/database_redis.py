"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: database_redis.py Redis连接池
描述: Redis 异步连接池 + Pub/Sub 独立连接 + 同步发布

包含:
- 函数: get_redis — 通用缓存
- 函数: get_redis_pubsub — Pub/Sub 专用
- 函数: redis_publish — 同步发布消息（供后台线程使用）
- 函数: close_redis — 关闭连接
"""

import redis
import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.config import config

_redis_pool: Redis | None = None
_redis_pubsub: Redis | None = None
_redis_sync: redis.Redis | None = None


# 获取 Redis 连接（通用缓存操作）。
async def get_redis() -> Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            config.redis.url,
            max_connections=config.redis.max_connections,
            decode_responses=True,
        )
    return _redis_pool


# 获取独立的 Redis Pub/Sub 连接。
async def get_redis_pubsub() -> Redis:
    global _redis_pubsub
    if _redis_pubsub is None:
        _redis_pubsub = aioredis.from_url(
            config.redis.url,
            max_connections=config.redis.max_connections,
            decode_responses=True,
        )
    return _redis_pubsub


# 同步 Redis 客户端（供同步上下文使用）
def get_redis_sync() -> redis.Redis:
    global _redis_sync
    if _redis_sync is None:
        _redis_sync = redis.Redis.from_url(config.redis.url, decode_responses=True)
    return _redis_sync


# 同步发布消息到频道（供后台线程使用，不依赖 asyncio event loop）
def redis_publish(channel: str, message: str) -> None:
    get_redis_sync().publish(channel, message)


# 关闭所有 Redis 连接。
async def close_redis() -> None:
    global _redis_pool, _redis_pubsub, _redis_sync
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
    if _redis_pubsub:
        await _redis_pubsub.close()
        _redis_pubsub = None
    if _redis_sync:
        _redis_sync.close()
        _redis_sync = None
