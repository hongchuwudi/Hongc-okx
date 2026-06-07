"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config.py 配置API
描述: 系统配置 API — GET/PUT /api/config

包含:
- GET /api/config → 返回当前配置
- PUT /api/config → 更新配置（部分字段）
- POST /api/config/reset → 重置为默认值
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigUpdate(BaseModel):
    """前端提交的配置更新（所有字段可选，只更新传入的）"""
    leverage: int | None = None
    order_amount: float | None = None
    max_position_ratio: float | None = None
    tick_interval_seconds: int | None = None
    max_daily_drawdown_pct: float | None = None
    max_daily_loss_usdt: float | None = None


@router.get("")
def get_config():
    """返回当前系统配置。"""
    from app.services.config_service import config_service
    return config_service.load()


@router.put("")
def update_config(body: ConfigUpdate):
    """更新系统配置（部分字段即可）。"""
    from app.services.config_service import config_service
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    return config_service.save(updates)


@router.post("/reset")
def reset_config():
    """重置所有配置为默认值。"""
    from app.services.config_service import config_service
    return config_service.reset()
