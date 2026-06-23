"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty_df.py 空 DataFrame
描述: 空 df 不抛异常，用 price 兜底
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_empty_df_fallback_to_price(mock_engine):
    sig = Signal(signal="BUY", confidence="LOW")
    fm = MagicMock(); fm.add.return_value = 1
    with patch("app.engine.loop.tick_memory.memory_service", fm):
        from app.engine.loop.tick_memory import tick_record_memory
        await tick_record_memory(mock_engine, pd.DataFrame(), 99.5, sig)
    assert fm.add.call_args.kwargs["price"] == 99.5
