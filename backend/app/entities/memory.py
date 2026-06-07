"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: memory.py 中文名
描述: AI Agent 记忆系统 — 记录每次决策及其结果，用于自我反思

包含:
- 类: TradeMemory — 单条交易记忆，记录 AI 决策及后续结果
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean
from app.entities import Base


# 单条交易记忆 — AI 的一次决策 + 结果
class TradeMemory(Base):
    __tablename__ = "trade_memories"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 决策时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    # AI 信号: BUY / SELL / HOLD
    signal = Column(String(10))
    # 信心水平: HIGH / MEDIUM / LOW
    confidence = Column(String(10))
    # AI 给出的决策理由
    reason = Column(Text)
    # 决策时的行情价格
    price = Column(Float)
    # 市场状态摘要，如 "下跌趋势 RSI=35 MACD=空"
    market_state = Column(String(50))
    # 交易盈亏（USDT），平仓后更新
    outcome_pnl = Column(Float, nullable=True)
    # AI 事后反思记录
    outcome_note = Column(Text, nullable=True)
    # 是否盈利
    is_win = Column(Boolean, nullable=True)
    # 平仓时间
    closed_at = Column(DateTime, nullable=True)
