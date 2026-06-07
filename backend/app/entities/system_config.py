"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: system_config.py 系统配置实体
描述: 交易参数配置表 — JSON 存储，支持 API 动态修改

包含:
- 类: SystemConfig — 系统配置 ORM 模型
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.entities import Base


class SystemConfig(Base):
    """系统运行配置，以 JSON 字符串存储所有交易参数。"""

    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_json = Column(Text, nullable=False, default="{}")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
