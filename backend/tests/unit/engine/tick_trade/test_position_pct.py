"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_position_pct.py 仓位缩放
描述: multi_agent 模式下按 position_pct 缩放金额
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_scales_by_position_pct(mock_engine):
    sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
    mock_engine.trade.execute = AsyncMock(return_value={"action":"open"})
    mock_engine.use_multi_agent = True
    decision = {"position_pct": 50}
    with patch("app.engine.loop.tick_trade.get_runtime_async") as mrt:
        mrt.side_effect = lambda k: {"order_amount":10.0,"leverage":10}[k]
        from app.engine.loop.tick_trade import tick_execute_trade
        await tick_execute_trade(mock_engine, sig, 100.0, decision)
    assert mock_engine.trade.execute.call_args.kwargs["amount_usdt"] == 5.0

@pytest.mark.asyncio
async def test_default_position_pct_is_100(mock_engine):
    sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
    mock_engine.trade.execute = AsyncMock(return_value={"action":"open"})
    mock_engine.use_multi_agent = True
    with patch("app.engine.loop.tick_trade.get_runtime_async") as mrt:
        mrt.side_effect = lambda k: {"order_amount":8.0,"leverage":10}[k]
        from app.engine.loop.tick_trade import tick_execute_trade
        await tick_execute_trade(mock_engine, sig, 100.0, {})
    assert mock_engine.trade.execute.call_args.kwargs["amount_usdt"] == 8.0
