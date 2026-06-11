"""
Created: 2026-06-14
Author: hongchuwudi
Description: 回测引擎辅助函数 — 类型转换、止盈止损检测、平仓盈亏计算

Contains:
- Function: _to_native — 递归将 numpy 类型转换为 Python 原生类型
- Function: _check_stop — 检测止盈止损是否触发
- Function: _close_position — 计算平仓盈亏（扣除手续费）
"""

import numpy as np
from typing import Any, Optional


def _to_native(v: Any) -> Any:
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, dict):
        return {k: _to_native(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_to_native(x) for x in v]
    return v


def _check_stop(price: float, high: float, low: float, position: Optional[dict]) -> Optional[float]:
    if not position:
        return None
    if position["side"] == "long":
        if low <= position["stop_loss"]:
            return position["stop_loss"]
        if high >= position["take_profit"]:
            return position["take_profit"]
    else:
        if high >= position["stop_loss"]:
            return position["stop_loss"]
        if low <= position["take_profit"]:
            return position["take_profit"]
    return None


def _to_ms(ts) -> int:
    """pandas Timestamp → 毫秒时间戳，避免字符串转换来回出错"""
    return int(ts.timestamp() * 1000)


def _close_position(position: dict, exit_price: float, fee_rate: float) -> float:
    if position["side"] == "long":
        pnl = (exit_price - position["entry_price"]) * position["size"]
    else:
        pnl = (position["entry_price"] - exit_price) * position["size"]
    fee = position["size"] * exit_price * fee_rate
    return pnl - fee
