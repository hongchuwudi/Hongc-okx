"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_open_not_update.py 开仓不更新记忆
描述: open/add 动作不清除 memory_id
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_open_keeps_memory_id(mock_engine):
    sig = Signal(signal="BUY", stop_loss=95.0, take_profit=105.0)
    mock_engine.trade.execute = AsyncMock(return_value={"action":"open"})
    mock_engine.use_multi_agent = False
    mock_engine._open_trade_memory_id = 5
    fm = MagicMock()
    with patch("app.engine.loop.tick_trade.get_runtime_async") as mrt, \
         patch("app.engine.loop.tick_trade.memory_service", fm):
        mrt.side_effect = lambda k: {"order_amount":1.0,"leverage":10}[k]
        from app.engine.loop.tick_trade import tick_execute_trade
        await tick_execute_trade(mock_engine, sig, 100.0, None)
    fm.update_outcome.assert_not_called()
    assert mock_engine._open_trade_memory_id == 5

@pytest.mark.asyncio
async def test_add_keeps_memory_id(mock_engine):
    sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
    mock_engine.trade.execute = AsyncMock(return_value={"action":"add"})
    mock_engine.use_multi_agent = False
    mock_engine._open_trade_memory_id = 5
    fm = MagicMock()
    with patch("app.engine.loop.tick_trade.get_runtime_async") as mrt, \
         patch("app.engine.loop.tick_trade.memory_service", fm):
        mrt.side_effect = lambda k: {"order_amount":1.0,"leverage":10}[k]
        from app.engine.loop.tick_trade import tick_execute_trade
        await tick_execute_trade(mock_engine, sig, 100.0, None)
    fm.update_outcome.assert_not_called()
    assert mock_engine._open_trade_memory_id == 5
