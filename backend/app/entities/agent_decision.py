"""
创建时间: 2026-06-16
作者: hongchuwudi
文件名: agent_decision.py Agent决策记录
描述: PostgreSQL ORM 模型 — 每个 tick 的 Agent 决策输出存档

包含:
- 类: AgentDecision — 单次 tick 的 Agent 决策记录
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.entities import Base


class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    mode = Column(String(20), default="")
    agents_json = Column(Text, default="")
    signal = Column(String(10), default="HOLD")
    confidence = Column(String(10), default="LOW")
    reason = Column(Text, default="")
    stop_loss = Column(Float, default=0)
    take_profit = Column(Float, default=0)
    source_count = Column(Integer, default=0)
