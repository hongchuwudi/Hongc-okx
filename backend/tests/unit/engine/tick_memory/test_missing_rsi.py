"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_missing_rsi.py RSI 缺失
描述: df 无 rsi 列时默认 RSI=50
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd; import numpy as np
from app.engine.result.signal import Signal

def _df_no_rsi(n=60):
    np.random.seed(1); close=np.cumsum(np.random.randn(n)*0.5)+100
    return pd.DataFrame({"close":close,"high":close+0.3,"low":close-0.3,"volume":np.random.rand(n)*100})

@pytest.mark.asyncio
async def test_missing_rsi_uses_default(mock_engine):
    sig = Signal(signal="BUY", confidence="HIGH")
    fm = MagicMock(); fm.add.return_value = 1
    with patch("app.engine.loop.tick_memory.memory_service", fm):
        from app.engine.loop.tick_memory import tick_record_memory
        await tick_record_memory(mock_engine, _df_no_rsi(), 100.0, sig)
    assert "RSI=50" in fm.add.call_args.kwargs["market_state"]
