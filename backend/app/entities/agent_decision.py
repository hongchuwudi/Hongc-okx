"""
创建时间: 2026-06-16
作者: hongchuwudi
文件名: agent_decision.py Agent决策记录
描述: Agent决策 ORM 模型 — 存储每个 tick 的 Agent 决策输出

包含:
- 类: AgentDecision — 单次 tick 的 Agent 决策记录
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.entities import Base


# Agent决策记录 — 存储每个 tick 的综合决策信号及代理投票详情
class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 决策时间戳
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    # 决策模式（如 single / voting / ensemble）
    mode = Column(String(20), default="")
    # 代理投票详情 JSON（各代理名称与信号）
    agents_json = Column(Text, default="")
    # 最终决策信号: BUY / SELL / HOLD
    signal = Column(String(10), default="HOLD")
    # 信号置信度: LOW / MEDIUM / HIGH
    confidence = Column(String(10), default="LOW")
    # 决策理由说明
    reason = Column(Text, default="")
    # 止损价（绝对值）
    stop_loss = Column(Float, default=0)
    # 止盈价（绝对值）
    take_profit = Column(Float, default=0)
    # 参与决策的代理数量
    source_count = Column(Integer, default=0)