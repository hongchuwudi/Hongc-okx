"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_leverage.py 杠杆切换
描述: 杠杆热切换 — 无持仓应用/有持仓暂缓/不变跳过
"""
import pytest
from unittest.mock import AsyncMock, patch
@pytest.mark.asyncio
async def test_leverage_unchanged_noop(mock_engine):
    mock_engine._last_leverage = 10
    with patch("app.engine.runtime.runtime_leverage.get_runtime_async", AsyncMock(return_value=10)):
        from app.engine.runtime.runtime_leverage import _sync_leverage
        await _sync_leverage(mock_engine)
    mock_engine.exchange.set_leverage.assert_not_called()

@pytest.mark.asyncio
async def test_leverage_apply_no_position(mock_engine):
    mock_engine._last_leverage = 5
    mock_engine.market_data.get_positions = AsyncMock(return_value=None)
    with patch("app.engine.runtime.runtime_leverage.get_runtime_async", AsyncMock(return_value=20)):
        from app.engine.runtime.runtime_leverage import _sync_leverage
        await _sync_leverage(mock_engine)
    assert mock_engine._last_leverage == 20
    mock_engine.exchange.set_leverage.assert_called_once_with(mock_engine._symbol, 20)

@pytest.mark.asyncio
async def test_leverage_postpone_has_position(mock_engine):
    mock_engine._last_leverage = 5
    mock_engine.market_data.get_positions = AsyncMock(return_value={"side":"long","size":0.1})
    with patch("app.engine.runtime.runtime_leverage.get_runtime_async", AsyncMock(return_value=20)):
        from app.engine.runtime.runtime_leverage import _sync_leverage
        await _sync_leverage(mock_engine)
    assert mock_engine._last_leverage == 20
    mock_engine.exchange.set_leverage.assert_not_called()
