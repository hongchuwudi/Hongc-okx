"""数据库连接管理 — PostgreSQL (SQLAlchemy) + Redis"""

from typing import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import config

# ── PostgreSQL (同步) ──────────────────────────────────────────

_sync_engine = create_engine(
    config.postgres.url,
    pool_size=config.postgres.pool_size,
    max_overflow=config.postgres.max_overflow,
    pool_pre_ping=True,
    echo=False,
)

SyncSession = sessionmaker(bind=_sync_engine, autocommit=False, autoflush=False)


def get_sync_session() -> Session:
    return SyncSession()


# ── PostgreSQL (异步) ──────────────────────────────────────────

_async_engine = create_async_engine(
    config.postgres.async_url,
    pool_size=config.postgres.pool_size,
    max_overflow=config.postgres.max_overflow,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=_async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ── Redis (异步) ───────────────────────────────────────────────

_redis_pool: Redis | None = None
_redis_pubsub: Redis | None = None


async def get_redis() -> Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            config.redis.url,
            max_connections=config.redis.max_connections,
            decode_responses=True,
        )
    return _redis_pool


async def get_redis_pubsub() -> Redis:
    """Pub/Sub 需要独立连接（订阅后连接被占用）"""
    global _redis_pubsub
    if _redis_pubsub is None:
        _redis_pubsub = aioredis.from_url(
            config.redis.url,
            max_connections=config.redis.max_connections,
            decode_responses=True,
        )
    return _redis_pubsub


async def close_redis() -> None:
    global _redis_pool, _redis_pubsub
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
    if _redis_pubsub:
        await _redis_pubsub.close()
        _redis_pubsub = None


# ── 初始化 ─────────────────────────────────────────────────────

def init_db() -> None:
    """创建所有表（在应用启动时调用）"""
    from app.models import Base

    Base.metadata.create_all(_sync_engine)
