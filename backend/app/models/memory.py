"""AI Agent 记忆系统 — 记录每次决策及其结果，用于自我反思"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean
from app.models import Base


class TradeMemory(Base):
    """单条交易记忆 — AI 的一次决策 + 结果"""
    __tablename__ = "trade_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    signal = Column(String(10))             # BUY / SELL / HOLD
    confidence = Column(String(10))          # HIGH / MEDIUM / LOW
    reason = Column(Text)                    # AI 给出的理由
    price = Column(Float)                    # 行情价格
    market_state = Column(String(50))        # 市场状态摘要: "下跌趋势 RSI=35 MACD=空"
    outcome_pnl = Column(Float, nullable=True)    # 交易盈亏 (USDT)
    outcome_note = Column(Text, nullable=True)    # AI 事后的反思
    is_win = Column(Boolean, nullable=True)       # 是否盈利
    closed_at = Column(DateTime, nullable=True)   # 平仓时间
