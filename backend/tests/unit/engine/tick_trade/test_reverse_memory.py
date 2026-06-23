"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_reverse_memory.py 反向平仓记忆
描述: reverse 动作时更新记忆 outcome
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_reverse_updates_memory(mock_engine):
    sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
    mock_engine.trade.execute = AsyncMock(return_value={"action":"reverse","pnl":-3.0})
    mock_engine.use_multi_agent = False
    mock_engine._open_trade_memory_id = 3
    fm = MagicMock()
    with patch("app.engine.loop.tick_trade.get_runtime_async") as mrt, \
         patch("app.engine.loop.tick_trade.memory_service", fm):
        mrt.side_effect = lambda k: {"order_amount":1.0,"leverage":10}[k]
        from app.engine.loop.tick_trade import tick_execute_trade
        await tick_execute_trade(mock_engine, sig, 100.0, None)
    fm.update_outcome.assert_called_once_with(3, -3.0)
    assert mock_engine._open_trade_memory_id is None
