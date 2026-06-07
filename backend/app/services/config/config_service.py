"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config_service.py 配置服务
描述: 系统配置的动态加载/保存 — 从 PG 读取，合并默认值，支持 API 修改

包含:
- 类: ConfigService — 配置读写服务
"""

import json
from dataclasses import asdict

from app.database import get_sync_session
from app.entities.system_config import SystemConfig
from app.config.config_trade import TradeConfig
from app.services.config.runtime import set_runtime_batch, delete_runtime

# 默认配置（从 TradeConfig 数据类提取为 dict）
_DEFAULTS = asdict(TradeConfig())


# 加载/保存系统配置，PG 存储 + 本地内存缓存。
class ConfigService:

    def __init__(self):
        # 内存缓存，避免每次读取都查数据库
        self._cache: dict | None = None

    # 从 PG 加载配置，合并默认值。首次调用查询数据库，后续走内存缓存。
    def load(self) -> dict:
        # 命中缓存直接返回
        if self._cache is not None:
            return self._cache

        session = get_sync_session()
        try:
            # 取最新一条配置记录
            row = session.query(SystemConfig).order_by(SystemConfig.id.desc()).first()
            if row and row.config_json:
                try:
                    stored = json.loads(row.config_json)
                    # 合并：PG 里的值覆盖默认值，新增的默认值自动补上
                    merged = {**_DEFAULTS, **stored}
                    self._cache = merged
                    return merged
                except json.JSONDecodeError:
                    pass
            # 无存储数据 → 返回默认值
            self._cache = dict(_DEFAULTS)
            return self._cache
        finally:
            session.close()

    # 更新配置并持久化（PG 新增记录 + Redis 同步写入）。
    # 只更新传入的字段，未传的字段保持原值不变。
    def save(self, updates: dict) -> dict:
        # 基于当前配置合并更新
        current = dict(self.load())
        current.update(updates)

        # 写入 PostgreSQL（追加新记录，保留历史）
        session = get_sync_session()
        try:
            cfg = SystemConfig(config_json=json.dumps(current, ensure_ascii=False))
            session.add(cfg)
            session.commit()
            self._cache = current
        finally:
            session.close()

        # 同步写入 Redis，引擎实时可读
        set_runtime_batch(updates)
        return current

    # 重置为默认值（清空缓存，删除 Redis 中的运行时配置）。
    def reset(self) -> dict:
        self._cache = None
        # 逐条删除 Redis 中的运行时配置键
        for key in _DEFAULTS:
            delete_runtime(key)
        # 重新加载默认值
        return self.reload()

    # 强制从 PG 重新加载，清除缓存。
    def reload(self) -> dict:
        self._cache = None
        return self.load()


# 全局单例
config_service = ConfigService()