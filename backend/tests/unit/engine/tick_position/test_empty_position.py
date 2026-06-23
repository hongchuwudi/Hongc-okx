"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty_position.py 空持仓
描述: position={} 或 size=0 时跳过
"""
import pytest
from unittest.mock import MagicMock
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_empty_dict_skips(mock_engine):
    sig = Signal(signal="HOLD", stop_loss=0, take_profit=0)
    from app.engine.loop.tick_position import tick_manage_position
    result = await tick_manage_position(mock_engine, {}, 100.0, MagicMock(), sig, MagicMock())
    assert result is sig

@pytest.mark.asyncio
async def test_zero_size_skips(mock_engine):
    sig = Signal(signal="BUY", stop_loss=95.0, take_profit=105.0)
    from app.engine.loop.tick_position import tick_manage_position
    result = await tick_manage_position(mock_engine, {"side":"long","size":0}, 100.0, MagicMock(), sig, MagicMock())
    assert result.stop_loss == 95.0
