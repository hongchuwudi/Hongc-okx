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

# 默认配置（从 dataclass 提取）
_DEFAULTS = asdict(TradeConfig())


class ConfigService:
    """加载/保存系统配置，PG 存储 + 本地缓存。"""

    def __init__(self):
        self._cache: dict | None = None

    def load(self) -> dict:
        """从 PG 加载配置，合并默认值。第一次调用缓存，后续走缓存。"""
        if self._cache is not None:
            return self._cache

        session = get_sync_session()
        try:
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
            # 无存储数据 → 用默认值
            self._cache = dict(_DEFAULTS)
            return self._cache
        finally:
            session.close()

    def save(self, updates: dict) -> dict:
        """更新配置并持久化。只更新传入的字段，其他保持不变。"""
        current = dict(self.load())
        current.update(updates)

        session = get_sync_session()
        try:
            cfg = SystemConfig(config_json=json.dumps(current, ensure_ascii=False))
            session.add(cfg)
            session.commit()
            self._cache = current
        finally:
            session.close()

        return current

    def reset(self) -> dict:
        """重置为默认值。"""
        self._cache = None
        return self.reload()

    def reload(self) -> dict:
        """强制从 PG 重新加载。"""
        self._cache = None
        return self.load()


config_service = ConfigService()
