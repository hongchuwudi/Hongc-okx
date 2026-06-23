"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_buy_stores_id.py BUY 信号
描述: BUY 写入记忆并设置 _open_trade_memory_id
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd; import numpy as np
from app.engine.result.signal import Signal

def _df(n=60):
    np.random.seed(1); close = np.cumsum(np.random.randn(n)*0.5)+100
    d = pd.DataFrame({"close":close,"high":close+0.3,"low":close-0.3,"volume":np.random.rand(n)*100})
    d["rsi"] = np.linspace(30,70,n); return d

@pytest.mark.asyncio
async def test_buy_stores_memory_id(mock_engine):
    sig = Signal(signal="BUY", confidence="HIGH", reason="突破")
    fm = MagicMock(); fm.add.return_value = 42
    with patch("app.engine.loop.tick_memory.memory_service", fm):
        from app.engine.loop.tick_memory import tick_record_memory
        await tick_record_memory(mock_engine, _df(), 101.0, sig)
    kw = fm.add.call_args.kwargs
    assert kw["signal"] == "BUY" and kw["confidence"] == "HIGH"
    assert mock_engine._open_trade_memory_id == 42
