"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_symbol.py 交易对切换
描述: 交易对热切换 — 无持仓应用/有持仓暂缓
"""
import pytest
from unittest.mock import AsyncMock, patch
@pytest.mark.asyncio
async def test_symbol_unchanged_noop(mock_engine):
    mock_engine._last_symbol = "DOGE/USDT:USDT"
    mock_engine._symbol = "DOGE/USDT:USDT"
    with patch("app.engine.runtime.runtime_symbol.get_runtime_async", AsyncMock(return_value="DOGE/USDT:USDT")):
        from app.engine.runtime.runtime_symbol import _sync_symbol
        await _sync_symbol(mock_engine)

@pytest.mark.asyncio
async def test_symbol_apply_no_position(mock_engine):
    mock_engine._last_symbol = "DOGE/USDT:USDT"
    mock_engine._symbol = "DOGE/USDT:USDT"
    mock_engine.market_data.get_positions = AsyncMock(return_value=None)
    with patch("app.engine.runtime.runtime_symbol.get_runtime_async", AsyncMock(return_value="ETH/USDT:USDT")):
        from app.engine.runtime.runtime_symbol import _sync_symbol
        await _sync_symbol(mock_engine)
    assert mock_engine._symbol == "ETH/USDT:USDT"

@pytest.mark.asyncio
async def test_symbol_postpone_has_position(mock_engine):
    o = "DOGE/USDT:USDT"
    mock_engine._last_symbol = o; mock_engine._symbol = o
    mock_engine.market_data.get_positions = AsyncMock(return_value={"side":"long","size":0.1})
    with patch("app.engine.runtime.runtime_symbol.get_runtime_async", AsyncMock(return_value="ETH/USDT:USDT")):
        from app.engine.runtime.runtime_symbol import _sync_symbol
        await _sync_symbol(mock_engine)
    assert mock_engine._symbol == o
