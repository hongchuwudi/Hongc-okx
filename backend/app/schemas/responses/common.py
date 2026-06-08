"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: 通用 schema — 健康检查
"""

from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """GET /api/health 响应"""
    ok: bool
    db: str = "postgresql"
    connected: bool
    error: Optional[str] = None
