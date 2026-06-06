"""PostgreSQL ORM 模型 — 交易相关"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.models import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    signal = Column(String(10))
    price = Column(Float)
    amount = Column(Float)
    confidence = Column(String(10))
    reason = Column(Text)
    pnl = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    equity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
