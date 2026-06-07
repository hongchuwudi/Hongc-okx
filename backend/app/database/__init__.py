"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: __init__.py 数据库模块导出
描述: 数据库连接管理 — 组合 PostgreSQL + Redis 子模块

包含:
- 函数: init_db — 创建所有表（启动时调用）
"""

from app.database.database_postgres import (
    SyncSession, AsyncSessionLocal,
    get_sync_session, get_async_session,
)
from app.database.database_redis import get_redis, get_redis_pubsub, close_redis


def init_db() -> None:
    """创建所有数据库表（在应用启动时调用）。"""
    from app.entities import Base
    from app.database.database_postgres import _sync_engine
    Base.metadata.create_all(_sync_engine)
