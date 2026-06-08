"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: Agent 私有记忆 ORM 模型 — 每个 Agent 独立的持久化记忆存储

包含:
- 类: AgentPrivateMemory — Agent 的 key-value 私有记忆记录
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text
from app.entities import Base


class AgentPrivateMemory(Base):
    __tablename__ = "agent_private_memory"

    agent_name = Column(String(32), primary_key=True)
    key = Column(String(128), primary_key=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow)
