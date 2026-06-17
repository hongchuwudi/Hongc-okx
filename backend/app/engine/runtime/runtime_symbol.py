"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: runtime_symbol.py 交易对热切换
描述: 检测交易对变化，无持仓时切换，有持仓时暂缓

包含:
- 函数: _sync_symbol — 交易对热切换
"""

from app.services.agent.agent_coordinator_service import create_position_manager
from app.services.config.runtime import get_runtime_async
from app.core.logger import get_logger

logger = get_logger()


async def _sync_symbol(engine) -> None:
    """交易对变化时热切换（仅无持仓时生效）。"""
    new_symbol = await get_runtime_async("symbol")
    if new_symbol == engine._last_symbol:
        return

    engine._last_symbol = new_symbol
    if new_symbol == engine._symbol:
        logger.info(f"[运行时] 交易对已为 {new_symbol}，无需切换")
        return

    try:
        pos = await engine.market_data.get_positions(engine._symbol)
        if pos and pos.get("side") and pos.get("size", 0) > 0:
            logger.warning(f"[运行时] 有持仓，交易对切换暂缓: {engine._symbol} -> {new_symbol}")
        else:
            engine._symbol = new_symbol
            engine.position_manager = create_position_manager(engine.exchange, new_symbol)
            logger.info(f"[运行时] 交易对切换 -> {new_symbol}")
    except Exception:
        engine._symbol = new_symbol
        engine.position_manager = create_position_manager(engine.exchange, new_symbol)
