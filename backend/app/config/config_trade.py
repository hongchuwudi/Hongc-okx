"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config_trade.py 交易配置
描述: 交易策略参数配置

包含:
- 类: TradeConfig — 交易对/杠杆/周期/仓位/风控参数
"""

import os
from dataclasses import dataclass


@dataclass
class TradeConfig:
    symbol: str = os.getenv("TRADE_SYMBOL", "BTC/USDT:USDT")
    leverage: int = int(os.getenv("TRADE_LEVERAGE", "1"))
    timeframe: str = "1h"
    data_points: int = 168
    tick_interval_seconds: int = 180  # 3 分钟
    order_amount: float = 1.0
    max_position_ratio: float = 0.8
    max_daily_drawdown_pct: float = float(os.getenv("MAX_DAILY_DRAWDOWN_PCT", "10.0"))
    max_daily_loss_usdt: float = float(os.getenv("MAX_DAILY_LOSS_USDT", "50.0"))
