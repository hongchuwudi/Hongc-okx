"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: trading.py 中文名
描述: PostgreSQL ORM 模型 — 交易记录和权益快照

包含:
- 类: Trade — 交易记录，存储每笔交易的详细数据
- 类: EquitySnapshot — 权益快照，记录各时间点的账户权益
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.entities import Base


class Trade(Base):
    """交易记录 — 存储每笔交易的详细数据"""
    __tablename__ = "trades"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 交易时间
    timestamp = Column(DateTime, index=True)
    # 信号方向: BUY / SELL
    signal = Column(String(10))
    # 交易价格
    price = Column(Float)
    # 交易数量
    amount = Column(Float)
    # 信号信心水平
    confidence = Column(String(10))
    # 交易理由
    reason = Column(Text)
    # 盈亏（USDT）
    pnl = Column(Float, default=0)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)


class EquitySnapshot(Base):
    """权益快照 — 记录各时间点的账户权益，用于生成权益曲线"""
    __tablename__ = "equity_snapshots"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 快照时间
    timestamp = Column(DateTime, index=True)
    # 账户权益
    equity = Column(Float)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
