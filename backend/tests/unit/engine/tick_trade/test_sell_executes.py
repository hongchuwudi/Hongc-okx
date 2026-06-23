"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_sell_executes.py SELL 执行
描述: SELL 信号正常执行
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_sell_executes(mock_engine):
    sig = Signal(signal="SELL", stop_loss=103.0, take_profit=95.0)
    mock_engine.trade.execute = AsyncMock(return_value={"action":"open"})
    mock_engine.use_multi_agent = False
    with patch("app.engine.loop.tick_trade.get_runtime_async") as mrt:
        mrt.side_effect = lambda k: {"order_amount":3.0,"leverage":5}[k]
        from app.engine.loop.tick_trade import tick_execute_trade
        result = await tick_execute_trade(mock_engine, sig, 200.0, None)
    assert result is not None
    assert mock_engine.trade.execute.call_args.kwargs["signal"] == "SELL"
