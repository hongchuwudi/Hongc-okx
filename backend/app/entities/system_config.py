"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: system_config.py 系统配置实体
描述: 交易参数配置表 — JSON 存储，支持 API 动态修改

包含:
- 类: SystemConfig — 系统配置 ORM 模型
"""

from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime

from app.entities import Base


# 系统运行配置，以 JSON 字符串存储所有交易参数。
class SystemConfig(Base):

    __tablename__ = "system_config"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    # JSON 配置字符串，存储全部交易参数
    config_json = Column(Text, nullable=False, default="{}")
    # 最后更新时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)