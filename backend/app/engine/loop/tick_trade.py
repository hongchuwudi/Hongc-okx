"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_trade.py 交易执行
描述: 每个 tick 执行交易信号（开仓 / 平仓 / 反向）

包含:
- 函数: tick_execute_trade — 根据信号执行交易
"""

from app.engine.result.signal import Signal
from app.services.config.runtime import get_runtime_async
from app.services.memory.memory import memory_service
from app.core.logger import get_logger

logger = get_logger()


async def tick_execute_trade(engine, signal: Signal, price: float,
                              decision: dict | None) -> dict | None:
    """执行交易。HOLD 信号跳过。返回交易结果或 None。"""
    if signal.signal == "HOLD":
        return None

    order_amount = float(await get_runtime_async("order_amount"))
    leverage = int(await get_runtime_async("leverage"))

    if engine.use_multi_agent and decision:
        position_pct = float(decision.get("position_pct", 100))
        order_amount = order_amount * (position_pct / 100)

    trade_result = await engine.trade.execute(
        signal=signal.signal, price=price,
        stop_loss=signal.stop_loss, take_profit=signal.take_profit,
        amount_usdt=order_amount, leverage=leverage,
    )

    if trade_result:
        logger.info(f"交易执行: {trade_result.get('action')}")
        action = trade_result.get("action", "")
        if action == "reverse" and engine._open_trade_memory_id is not None:
            memory_service.update_outcome(engine._open_trade_memory_id, trade_result.get("pnl", 0))
            engine._open_trade_memory_id = None

    return trade_result
