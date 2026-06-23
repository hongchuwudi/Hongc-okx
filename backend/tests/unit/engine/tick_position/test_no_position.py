"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_no_position.py 无持仓
描述: position=None 时返回原 signal 不变
"""
import pytest
from unittest.mock import MagicMock
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_no_position_unchanged(mock_engine):
    sig = Signal(signal="BUY", stop_loss=95.0, take_profit=105.0)
    from app.engine.loop.tick_position import tick_manage_position
    result = await tick_manage_position(mock_engine, None, 100.0, MagicMock(), sig, MagicMock())
    assert result is sig and result.stop_loss == 95.0
