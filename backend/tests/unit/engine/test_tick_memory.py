"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_tick_memory.py AI 决策记忆测试
描述: 验证 tick_memory 的记忆记录 — 正常写入 / HOLD 不记 / 缺失 RSI 降级

包含:
- TestMemoryNormal — 正常记忆记录
- TestMemoryHold — HOLD 信号不设 memory_id
- TestMemoryMissingRSI — RSI 列缺失时降级
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from app.engine.result.signal import Signal


def _make_df(n=60, with_rsi=True):
    """构造有 SMA20 可计算的 OHLCV DataFrame。"""
    np.random.seed(1)
    close = np.cumsum(np.random.randn(n) * 0.5) + 100
    d = pd.DataFrame({
        "close": close,
        "high": close + 0.3,
        "low": close - 0.3,
        "volume": np.random.rand(n) * 100,
    })
    if with_rsi:
        d["rsi"] = np.linspace(30, 70, n)
    return d


class TestMemoryNormal:
    """正常记录记忆。"""

    @pytest.mark.asyncio
    async def test_records_buy_signal_and_stores_id(self, mock_engine):
        """BUY 信号写入记忆并设置 _open_trade_memory_id。"""
        df = _make_df()
        sig = Signal(signal="BUY", confidence="HIGH", reason="突破阻力")
        fake_memory = MagicMock()
        fake_memory.add.return_value = 42

        with patch("app.engine.loop.tick_memory.memory_service", fake_memory):
            from app.engine.loop.tick_memory import tick_record_memory
            await tick_record_memory(mock_engine, df, 101.0, sig)

        fake_memory.add.assert_called_once()
        call_kwargs = fake_memory.add.call_args.kwargs
        assert call_kwargs["signal"] == "BUY"
        assert call_kwargs["confidence"] == "HIGH"
        assert call_kwargs["reason"] == "突破阻力"
        assert call_kwargs["price"] == pytest.approx(float(df["close"].iloc[-1]))
        assert mock_engine._open_trade_memory_id == 42

    @pytest.mark.asyncio
    async def test_market_summary_contains_trend_and_rsi(self, mock_engine):
        """市场摘要含趋势方向和 RSI 值。"""
        df = _make_df(with_rsi=True)
        sig = Signal(signal="SELL", confidence="MEDIUM", reason="")
        fake_memory = MagicMock()
        fake_memory.add.return_value = 7

        with patch("app.engine.loop.tick_memory.memory_service", fake_memory):
            from app.engine.loop.tick_memory import tick_record_memory
            await tick_record_memory(mock_engine, df, 100.0, sig)

        call_kwargs = fake_memory.add.call_args.kwargs
        assert "趋势" in call_kwargs["market_state"]
        assert "RSI=" in call_kwargs["market_state"]


class TestMemoryHold:
    """HOLD 信号不设 memory_id。"""

    @pytest.mark.asyncio
    async def test_hold_does_not_store_id(self, mock_engine):
        """HOLD 信号仍写入记忆但不设置 _open_trade_memory_id。"""
        mock_engine._open_trade_memory_id = None
        df = _make_df()
        sig = Signal(signal="HOLD", confidence="LOW", reason="等待")
        fake_memory = MagicMock()
        fake_memory.add.return_value = 99

        with patch("app.engine.loop.tick_memory.memory_service", fake_memory):
            from app.engine.loop.tick_memory import tick_record_memory
            await tick_record_memory(mock_engine, df, 100.0, sig)

        fake_memory.add.assert_called_once()
        assert mock_engine._open_trade_memory_id is None


class TestMemoryMissingRSI:
    """RSI 列缺失时降级。"""

    @pytest.mark.asyncio
    async def test_missing_rsi_column_uses_default(self, mock_engine):
        """df 无 rsi 列时 RSI 默认为 50，不抛异常。"""
        df = _make_df(with_rsi=False)
        sig = Signal(signal="BUY", confidence="HIGH", reason="测试")
        fake_memory = MagicMock()
        fake_memory.add.return_value = 1

        with patch("app.engine.loop.tick_memory.memory_service", fake_memory):
            from app.engine.loop.tick_memory import tick_record_memory
            await tick_record_memory(mock_engine, df, 100.0, sig)

        call_kwargs = fake_memory.add.call_args.kwargs
        assert "RSI=50" in call_kwargs["market_state"]

    @pytest.mark.asyncio
    async def test_empty_df_uses_price_fallback(self, mock_engine):
        """空 df 时不抛异常，用 price 作为 last_close。"""
        df = pd.DataFrame()
        sig = Signal(signal="BUY", confidence="LOW", reason="测试")
        fake_memory = MagicMock()
        fake_memory.add.return_value = 1

        with patch("app.engine.loop.tick_memory.memory_service", fake_memory):
            from app.engine.loop.tick_memory import tick_record_memory
            await tick_record_memory(mock_engine, df, 99.5, sig)

        fake_memory.add.assert_called_once()
        assert fake_memory.add.call_args.kwargs["price"] == 99.5
