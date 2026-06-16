"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_position.py 动态持仓管理
描述: 每个 tick 更新追踪止损/止盈（有持仓时）

包含:
- 函数: tick_manage_position — 调用 PositionManager 更新止盈止损
"""

import pandas as pd

from app.engine.result.signal import Signal
from app.core.logger import get_logger

logger = get_logger()


async def tick_manage_position(engine, position: dict | None, price: float,
                                df: pd.DataFrame, signal: Signal,
                                indicator_service) -> Signal:
    """动态持仓管理：有持仓时更新移动止盈止损。

    直接修改 signal 的 stop_loss / take_profit 并返回。
    """
    if not position or not position.get("side") or position.get("size", 0) <= 0:
        return signal

    atr_pct = indicator_service.atr_pct(df)
    pm_result = await engine.position_manager.update(
        position=position, current_price=price, atr_pct=atr_pct,
        current_sl=signal.stop_loss, current_tp=signal.take_profit,
    )
    if pm_result.get("updated"):
        signal.stop_loss = pm_result["stop_loss"]
        signal.take_profit = pm_result["take_profit"]

    return signal
