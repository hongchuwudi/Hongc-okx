"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config.py 配置API
描述: 系统配置 API — GET/PUT /api/config

包含:
- 端点: GET /api/config → 返回当前配置
- 端点: PUT /api/config → 更新配置（部分字段）
- 端点: POST /api/config/reset → 重置为默认值
"""

from fastapi import APIRouter

from app.schemas.requests.config import ConfigUpdate

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
