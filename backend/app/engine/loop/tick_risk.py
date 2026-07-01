"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_risk.py 风控检查
描述: 每个 tick 的风控检查（熔断、回撤限制、日亏损上限）

包含:
- 函数: tick_check_risk — 执行风控检查，返回是否通过
"""

from app.engine.result.signal import Signal
from app.services.persistence import persist_tick, publish_event
from app.core.logger import get_logger

logger = get_logger()


async def tick_check_risk(engine, signal: Signal, account: dict,
                           position: dict | None, price: float) -> bool:
    """风控检查。返回 True 表示通过，False 表示拦截。

    拦截时自动 persist_tick 当前状态。
    """
    risk_result = await engine.risk.check(
        signal=signal.signal, equity=account["equity"],
        current_position_value=abs(position["size"] * (position.get("entry_price") or price)) if position else 0,
    )
    if not risk_result.passed:
        logger.warning(f"风控拦截: {risk_result.reason}")
        if "熔断" in risk_result.reason:
            await publish_event({"type": "circuit_breaker", "reason": risk_result.reason})
        await persist_tick(price, account, position, signal, None)
        return False
    return True
