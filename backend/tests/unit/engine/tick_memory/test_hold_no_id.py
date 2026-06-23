"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_hold_no_id.py HOLD 信号
描述: HOLD 记录但不设 memory_id
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd; import numpy as np
from app.engine.result.signal import Signal

def _df(n=60):
    np.random.seed(1); close=np.cumsum(np.random.randn(n)*0.5)+100
    d=pd.DataFrame({"close":close,"high":close+0.3,"low":close-0.3,"volume":np.random.rand(n)*100})
    d["rsi"]=np.linspace(30,70,n); return d

@pytest.mark.asyncio
async def test_hold_does_not_store_id(mock_engine):
    mock_engine._open_trade_memory_id = None
    sig = Signal(signal="HOLD", confidence="LOW", reason="等待")
    fm = MagicMock(); fm.add.return_value = 99
    with patch("app.engine.loop.tick_memory.memory_service", fm):
        from app.engine.loop.tick_memory import tick_record_memory
        await tick_record_memory(mock_engine, _df(), 100.0, sig)
    fm.add.assert_called_once()
    assert mock_engine._open_trade_memory_id is None
