"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: database_postgres.py PostgreSQL连接池
描述: PostgreSQL 同步+异步双引擎，连接池收敛在 config

包含:
- 变量: _sync_engine — 同步引擎
- 变量: SyncSession — 同步会话工厂
- 函数: get_sync_session — 获取同步会话
- 变量: _async_engine — 异步引擎
- 变量: AsyncSessionLocal — 异步会话工厂
- 函数: get_async_session — 获取异步会话
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import config

# ── 同步引擎 ──
_sync_engine = create_engine(
    config.postgres.url,
    pool_size=config.postgres.pool_size,
    max_overflow=config.postgres.max_overflow,
    pool_pre_ping=True,
    echo=False,
)
SyncSession = sessionmaker(bind=_sync_engine, autocommit=False, autoflush=False)


# 获取同步数据库会话。
def get_sync_session() -> Session:
    return SyncSession()


# ── 异步引擎 ──
_async_engine = create_async_engine(
    config.postgres.async_url,
    pool_size=config.postgres.pool_size,
    max_overflow=config.postgres.max_overflow,
    pool_pre_ping=True,
    echo=False,
)
AsyncSessionLocal = async_sessionmaker(bind=_async_engine, class_=AsyncSession, expire_on_commit=False)


# 获取异步数据库会话（FastAPI 依赖注入）。
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
