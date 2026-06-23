"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_buy_executes.py BUY 执行
描述: BUY 信号正确传参给 trade.execute
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_buy_executes_with_correct_params(mock_engine):
    sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
    mock_engine.trade.execute = AsyncMock(return_value={"action":"open"})
    mock_engine.use_multi_agent = False
    with patch("app.engine.loop.tick_trade.get_runtime_async") as mrt:
        mrt.side_effect = lambda k: {"order_amount":5.0,"leverage":10}[k]
        from app.engine.loop.tick_trade import tick_execute_trade
        await tick_execute_trade(mock_engine, sig, 100.0, None)
    kw = mock_engine.trade.execute.call_args.kwargs
    assert kw["signal"] == "BUY" and kw["price"] == 100.0
    assert kw["stop_loss"] == 97.0 and kw["take_profit"] == 105.0
    assert kw["amount_usdt"] == 5.0 and kw["leverage"] == 10
