"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_memory.py AI 决策记忆
描述: 每个 tick 记录 AI 信号到记忆库，用于长期学习优化

包含:
- 函数: tick_record_memory — 将当前信号写入记忆服务
"""

import pandas as pd

from app.engine.result.signal import Signal
from app.services.memory.memory import memory_service


async def tick_record_memory(engine, df: pd.DataFrame, price: float, signal: Signal) -> None:
    """记录 AI 决策到记忆库，平仓时关联盈亏结果。"""
    last_close = float(df["close"].iloc[-1]) if len(df) > 0 else price
    market_summary = ""
    try:
        sma20 = float(df["close"].rolling(20).mean().iloc[-1])
        trend = "上涨" if last_close > sma20 else "下跌"
        rsi_val = float(df["rsi"].iloc[-1]) if "rsi" in df.columns else 50
        market_summary = f"{trend}趋势 RSI={rsi_val:.0f}"
    except Exception:
        pass

    memory_id = memory_service.add(
        signal=signal.signal, confidence=signal.confidence,
        reason=signal.reason, price=last_close, market_state=market_summary,
    )
    if signal.signal != "HOLD":
        engine._open_trade_memory_id = memory_id
