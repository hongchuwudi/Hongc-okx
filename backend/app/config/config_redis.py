"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config_redis.py Redis配置
描述: Redis 连接配置

包含:
- 类: RedisConfig — Redis 连接参数
"""

import os
from dataclasses import dataclass


@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    db: int = int(os.getenv("REDIS_DB", "0"))
    max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
