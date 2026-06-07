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
    url: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
