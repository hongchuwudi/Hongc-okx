"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: database.py PostgreSQL与Redis连接池
描述: 数据库连接管理 — PostgreSQL (SQLAlchemy 同步+异步) + Redis 连接池与 Pub/Sub

包含:
- 函数: get_sync_session — 获取同步数据库会话
- 函数: get_async_session — 获取异步数据库会话（FastAPI 依赖注入）
- 函数: get_redis — 获取 Redis 连接
- 函数: get_redis_pubsub — 获取 Redis Pub/Sub 独立连接
- 函数: close_redis — 关闭所有 Redis 连接
- 函数: init_db — 初始化数据库表结构
- 常量: _sync_engine — 同步 SQLAlchemy 引擎
- 常量: _async_engine — 异步 SQLAlchemy 引擎
- 常量: SyncSession — 同步会话工厂
- 常量: AsyncSessionLocal — 异步会话工厂
"""

from typing import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import config

# ── PostgreSQL (同步) ──────────────────────────────────────────

# 同步 SQLAlchemy 引擎
_sync_engine = create_engine(
    config.postgres.url,
    pool_size=config.postgres.pool_size,
    max_overflow=config.postgres.max_overflow,
    pool_pre_ping=True,
    echo=False,
)

# 同步会话工厂
SyncSession = sessionmaker(bind=_sync_engine, autocommit=False, autoflush=False)


def get_sync_session() -> Session:
    """获取一个同步数据库会话"""
    return SyncSession()


# ── PostgreSQL (异步) ──────────────────────────────────────────

# 异步 SQLAlchemy 引擎（asyncpg 驱动）
_async_engine = create_async_engine(
    config.postgres.async_url,
    pool_size=config.postgres.pool_size,
    max_overflow=config.postgres.max_overflow,
    pool_pre_ping=True,
    echo=False,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=_async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话，用于 FastAPI 依赖注入"""
    async with AsyncSessionLocal() as session:
        yield session


# ── Redis (异步) ───────────────────────────────────────────────

_redis_pool: Redis | None = None  # 通用 Redis 连接池
_redis_pubsub: Redis | None = None  # Pub/Sub 独立连接（订阅后连接被占用）


async def get_redis() -> Redis:
    """获取 Redis 连接（通用缓存操作）"""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            config.redis.url,
            max_connections=config.redis.max_connections,
            decode_responses=True,
        )
    return _redis_pool


async def get_redis_pubsub() -> Redis:
    """获取独立的 Redis Pub/Sub 连接（订阅消息后该连接被独占）"""
    global _redis_pubsub
    if _redis_pubsub is None:
        _redis_pubsub = aioredis.from_url(
            config.redis.url,
            max_connections=config.redis.max_connections,
            decode_responses=True,
        )
    return _redis_pubsub


async def close_redis() -> None:
    """关闭所有 Redis 连接（应用停止时调用）"""
    global _redis_pool, _redis_pubsub
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
    if _redis_pubsub:
        await _redis_pubsub.close()
        _redis_pubsub = None


# ── 初始化 ─────────────────────────────────────────────────────

def init_db() -> None:
    """创建所有数据库表（在应用启动时调用）"""
    from app.models import Base

    Base.metadata.create_all(_sync_engine)
