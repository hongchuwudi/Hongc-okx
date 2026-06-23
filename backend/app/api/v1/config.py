"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config.py 配置API
描述: 系统配置 API — GET/PUT /api/config

包含:
- 端点: GET /api/config → 返回当前配置
- 端点: PUT /api/config → 更新配置（部分字段）
- 端点: POST /api/config/reset → 重置为默认值
- 端点: GET /api/config/runtime → Redis 运行时配置
- 端点: PUT /api/config/runtime → 写入 Redis 运行时配置
- 端点: DELETE /api/config/runtime/{key} → 删除运行时配置 key
- 端点: GET /api/config/ai-balance → DeepSeek 账户余额
"""

from fastapi import APIRouter

from app.schemas.requests.config import ConfigUpdate
from app.schemas.responses.agent import DeepSeekBalanceResponse

router = APIRouter(prefix="/api/v1/config", tags=["config"])


# 返回当前系统配置。
@router.get("")
def get_config():
    from app.services.config.config_service import config_service
    return config_service.load()


# 更新系统配置（部分字段即可）。
@router.put("")
def update_config(body: ConfigUpdate):
    from app.services.config.config_service import config_service
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    return config_service.save(updates)


# 重置所有配置为默认值。
@router.post("/reset")
def reset_config():
    from app.services.config.config_service import config_service
    return config_service.reset()


# 返回 Redis 运行时配置（实时生效的值，Redis 优先 + env fallback）。
@router.get("/runtime")
def get_runtime_config():
    from app.services.config.runtime import get_all_runtime
    return get_all_runtime()


# 直接写入 Redis 运行时配置（不持久化到 PG，重启后恢复 env 默认值）。
@router.put("/runtime")
def update_runtime_config(body: ConfigUpdate):
    from app.services.config.runtime import set_runtime_batch
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    set_runtime_batch(updates)
    return {"ok": True, "updated": list(updates.keys())}


# 删除单个运行时配置 key，恢复 env 默认值。
@router.delete("/runtime/{key}")
def delete_runtime_config(key: str):
    from app.services.config.runtime import delete_runtime
    delete_runtime(key)
    return {"ok": True, "deleted": key}


# 查询 DeepSeek 账户余额 — 供前端展示 AI 剩余金额与降级状态。
@router.get("/ai-balance", response_model=DeepSeekBalanceResponse)
def get_ai_balance():
    from app.services.agent.agent_balance_service import (
        get_deepseek_balance, BALANCE_DEGRADE_THRESHOLD,
    )
    info = get_deepseek_balance()
    return DeepSeekBalanceResponse(
        is_available=info["is_available"],
        total_balance=info["total_balance"],
        currency=info["currency"],
        granted_balance=info["granted_balance"],
        topped_up_balance=info["topped_up_balance"],
        degrade_threshold=BALANCE_DEGRADE_THRESHOLD,
        degraded=info["total_balance"] < BALANCE_DEGRADE_THRESHOLD,
    )
