"""
创建时间: 2026-06-07
作者: hongchuwudi
描述: 共享内核 — 异常 + 日志 + 配置 + 数据库

- exceptions.py — AppError 异常体系
- logger.py    — 全局日志
- config/      — 环境配置（AI/OKX/Postgres/Redis/Trade）
- database/    — PostgreSQL + Redis 连接管理
"""

from app.core.logger import get_logger  # noqa: F401
from app.core.exceptions import (       # noqa: F401
    AppError, NotFoundError, BusinessError, ExternalServiceError, ConfigError,
)
