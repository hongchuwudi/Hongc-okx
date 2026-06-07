"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config_postgres.py PostgreSQL配置
描述: PostgreSQL 连接配置

包含:
- 类: PostgresConfig — PG 连接参数
"""

import os
from dataclasses import dataclass


@dataclass
class PostgresConfig:
    host: str = os.getenv("PG_HOST", "127.0.0.1")
    port: int = int(os.getenv("PG_PORT", "5432"))
    user: str = os.getenv("PG_USER", "postgres")
    password: str = os.getenv("PG_PASSWORD", "")
    database: str = os.getenv("PG_DATABASE", "trading")
    pool_size: int = int(os.getenv("PG_POOL_SIZE", "10"))
    max_overflow: int = int(os.getenv("PG_MAX_OVERFLOW", "20"))

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
