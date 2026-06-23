"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_hold_skips.py HOLD 跳过
描述: HOLD 信号返回 None 且不调用 trade.execute
"""
import pytest
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_hold_returns_none(mock_engine):
    sig = Signal(signal="HOLD")
    from app.engine.loop.tick_trade import tick_execute_trade
    result = await tick_execute_trade(mock_engine, sig, 100.0, None)
    assert result is None
    mock_engine.trade.execute.assert_not_called()
