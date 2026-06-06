"""PostgreSQL ORM 模型 — 系统状态 (单行表)"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.models import Base

class SystemStatus(Base):
    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, default=1)
    status = Column(String(20), default="stopped")
    last_update = Column(DateTime)
    balance = Column(Float, default=0)
    equity = Column(Float, default=0)
    leverage = Column(Integer, default=1)
    btc_price = Column(Float, default=0)
    btc_change = Column(Float, default=0)
    timeframe = Column(String(10), default="1h")
    mode = Column(String(30), default="cross-oneway")
    position_side = Column(String(10), nullable=True)
    position_size = Column(Float, default=0)
    position_entry_price = Column(Float, default=0)
    position_unrealized_pnl = Column(Float, default=0)
    ai_signal = Column(String(10), default="HOLD")
    ai_confidence = Column(String(10), default="N/A")
    ai_reason = Column(Text, default="")
    ai_stop_loss = Column(Float, default=0)
    ai_take_profit = Column(Float, default=0)
    ai_timestamp = Column(DateTime)
    tp_sl_stop_loss_order_id = Column(String(64), nullable=True)
    tp_sl_take_profit_order_id = Column(String(64), nullable=True)
