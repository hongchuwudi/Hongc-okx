"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_tick_position.py 动态持仓管理测试
描述: 验证持仓管理各分支 — 无持仓跳过 / 有持仓更新止盈止损 / ATR 联动

包含:
- TestPositionNoop — 无持仓时跳过
- TestPositionUpdate — 有持仓时更新 sl/tp
- TestPositionNoUpdate — pm 未更新时保持原信号
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.engine.result.signal import Signal


class TestPositionNoop:
    """无持仓或无有效持仓时跳过，signal 不变。"""

    @pytest.mark.asyncio
    async def test_no_position_returns_unchanged(self, mock_engine):
        """position=None 时直接返回原 signal。"""
        sig = Signal(signal="BUY", stop_loss=95.0, take_profit=105.0)
        indicator = MagicMock()
        from app.engine.loop.tick_position import tick_manage_position
        result = await tick_manage_position(
            mock_engine, None, 100.0, MagicMock(), sig, indicator,
        )
        assert result is sig
        assert result.stop_loss == 95.0
        assert result.take_profit == 105.0

    @pytest.mark.asyncio
    async def test_empty_position_returns_unchanged(self, mock_engine):
        """position={} 时跳过。"""
        sig = Signal(signal="HOLD", stop_loss=0, take_profit=0)
        indicator = MagicMock()
        from app.engine.loop.tick_position import tick_manage_position
        result = await tick_manage_position(
            mock_engine, {}, 100.0, MagicMock(), sig, indicator,
        )
        assert result is sig

    @pytest.mark.asyncio
    async def test_zero_size_returns_unchanged(self, mock_engine):
        """position.size=0 时跳过。"""
        sig = Signal(signal="BUY", stop_loss=95.0, take_profit=105.0)
        indicator = MagicMock()
        from app.engine.loop.tick_position import tick_manage_position
        result = await tick_manage_position(
            mock_engine, {"side": "long", "size": 0}, 100.0, MagicMock(), sig, indicator,
        )
        assert result.stop_loss == 95.0  # 未修改


class TestPositionUpdate:
    """有持仓时调用 ATR + position_manager 并更新 sl/tp。"""

    @pytest.mark.asyncio
    async def test_updates_sl_tp_when_pm_updated(self, mock_engine):
        """position_manager 返回 updated=True 时修改 signal。"""
        sig = Signal(signal="BUY", stop_loss=95.0, take_profit=105.0)
        position = {"side": "long", "size": 0.1, "entry_price": 100.0}

        indicator = MagicMock()
        indicator.atr_pct.return_value = 0.03

        mock_engine.position_manager.update = AsyncMock(return_value={
            "updated": True, "stop_loss": 97.0, "take_profit": 108.0,
        })

        from app.engine.loop.tick_position import tick_manage_position
        result = await tick_manage_position(
            mock_engine, position, 100.0, MagicMock(), sig, indicator,
        )

        assert result.stop_loss == 97.0
        assert result.take_profit == 108.0

    @pytest.mark.asyncio
    async def test_calls_atr_pct_with_df(self, mock_engine):
        """验证 ATR 计算被调用，传入正确的 df。"""
        sig = Signal(signal="HOLD")
        position = {"side": "long", "size": 0.1}
        df = MagicMock()

        indicator = MagicMock()
        indicator.atr_pct.return_value = 0.02
        mock_engine.position_manager.update = AsyncMock(return_value={
            "updated": False,
        })

        from app.engine.loop.tick_position import tick_manage_position
        await tick_manage_position(mock_engine, position, 100.0, df, sig, indicator)

        indicator.atr_pct.assert_called_once_with(df)

    @pytest.mark.asyncio
    async def test_passes_current_sl_tp_to_pm(self, mock_engine):
        """验证 position_manager.update 收到当前 sl/tp。"""
        sig = Signal(signal="BUY", stop_loss=94.0, take_profit=110.0)
        position = {"side": "long", "size": 0.5, "entry_price": 100.0}

        indicator = MagicMock()
        indicator.atr_pct.return_value = 0.025
        mock_engine.position_manager.update = AsyncMock(return_value={
            "updated": False,
        })

        from app.engine.loop.tick_position import tick_manage_position
        await tick_manage_position(mock_engine, position, 102.0, MagicMock(), sig, indicator)

        call_kwargs = mock_engine.position_manager.update.call_args.kwargs
        assert call_kwargs["position"] is position
        assert call_kwargs["current_price"] == 102.0
        assert call_kwargs["current_sl"] == 94.0
        assert call_kwargs["current_tp"] == 110.0
        assert call_kwargs["atr_pct"] == 0.025


class TestPositionNoUpdate:
    """position_manager 返回 updated=False 时保持原信号。"""

    @pytest.mark.asyncio
    async def test_keeps_original_signal_when_not_updated(self, mock_engine):
        """pm 未更新时 signal.sl/tp 不变。"""
        sig = Signal(signal="SELL", stop_loss=105.0, take_profit=95.0)
        position = {"side": "short", "size": 0.2}

        indicator = MagicMock()
        indicator.atr_pct.return_value = 0.01
        mock_engine.position_manager.update = AsyncMock(return_value={
            "updated": False, "stop_loss": 999, "take_profit": 1,
        })

        from app.engine.loop.tick_position import tick_manage_position
        result = await tick_manage_position(
            mock_engine, position, 100.0, MagicMock(), sig, indicator,
        )

        # 即使 pm 返回了新值，updated=False 时不应用
        assert result.stop_loss == 105.0
        assert result.take_profit == 95.0
