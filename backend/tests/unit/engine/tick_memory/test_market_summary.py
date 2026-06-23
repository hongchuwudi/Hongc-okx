"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_market_summary.py 市场摘要
描述: 摘要含趋势方向 + RSI 值
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
async def test_summary_has_trend_and_rsi(mock_engine):
    sig = Signal(signal="SELL", confidence="MEDIUM")
    fm = MagicMock(); fm.add.return_value = 7
    with patch("app.engine.loop.tick_memory.memory_service", fm):
        from app.engine.loop.tick_memory import tick_record_memory
        await tick_record_memory(mock_engine, _df(), 100.0, sig)
    kw = fm.add.call_args.kwargs
    assert "趋势" in kw["market_state"] and "RSI=" in kw["market_state"]
