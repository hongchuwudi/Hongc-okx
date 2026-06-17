"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: runtime_leverage.py 杠杆热切换
描述: 检测杠杆变化，无持仓时调用 OKX API 设置

包含:
- 函数: _sync_leverage — 杠杆热切换
"""

from app.services.config.runtime import get_runtime_async
from app.core.logger import get_logger

logger = get_logger()


async def _sync_leverage(engine) -> None:
    """杠杆变化时热切换（仅无持仓时生效）。"""
    new_lev_raw = await get_runtime_async("leverage")
    new_lev = int(new_lev_raw) if new_lev_raw is not None else engine._last_leverage
    if new_lev == engine._last_leverage:
        return

    engine._last_leverage = new_lev
    try:
        pos = await engine.market_data.get_positions(engine._symbol)
        if pos and pos.get("side") and pos.get("size", 0) > 0:
            logger.warning(f"[运行时] 有持仓，杠杆切换暂缓 -> {new_lev}x")
        else:
            await engine.exchange.set_leverage(engine._symbol, new_lev)
            logger.info(f"[运行时] 杠杆切换 -> {new_lev}x")
    except Exception as e:
        logger.warning(f"[运行时] 杠杆切换失败: {e}")
