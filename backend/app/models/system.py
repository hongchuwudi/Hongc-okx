"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: system.py 中文名
描述: PostgreSQL ORM 模型 — 系统状态单行表，记录当前运行状态

包含:
- 类: SystemStatus — 系统状态，单行表存储当前运行状态
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.models import Base


class SystemStatus(Base):
    """系统状态 — 单行表，记录引擎当前运行状态和最新数据"""
    __tablename__ = "system_status"

    # 主键（固定为 1，单行模式）
    id = Column(Integer, primary_key=True, default=1)
    # 运行状态: running / stopped
    status = Column(String(20), default="stopped")
    # 最后更新时间
    last_update = Column(DateTime)
    # 账户余额
    balance = Column(Float, default=0)
    # 账户权益
    equity = Column(Float, default=0)
    # 杠杆倍数
    leverage = Column(Integer, default=1)
    # BTC 当前价格
    btc_price = Column(Float, default=0)
    # BTC 价格变化率
    btc_change = Column(Float, default=0)
    # K 线时间周期
    timeframe = Column(String(10), default="1h")
    # 交易模式
    mode = Column(String(30), default="cross-oneway")
    # 持仓方向
    position_side = Column(String(10), nullable=True)
    # 持仓数量
    position_size = Column(Float, default=0)
    # 持仓开仓均价
    position_entry_price = Column(Float, default=0)
    # 持仓未实现盈亏
    position_unrealized_pnl = Column(Float, default=0)
    # AI 最新信号
    ai_signal = Column(String(10), default="HOLD")
    # AI 信心水平
    ai_confidence = Column(String(10), default="N/A")
    # AI 决策理由
    ai_reason = Column(Text, default="")
    # AI 建议止损价
    ai_stop_loss = Column(Float, default=0)
    # AI 建议止盈价
    ai_take_profit = Column(Float, default=0)
    # AI 决策时间
    ai_timestamp = Column(DateTime)
    # 止损算法订单 ID
    tp_sl_stop_loss_order_id = Column(String(64), nullable=True)
    # 止盈算法订单 ID
    tp_sl_take_profit_order_id = Column(String(64), nullable=True)
