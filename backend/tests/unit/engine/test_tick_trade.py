"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_tick_trade.py 交易执行测试
描述: 验证交易执行各分支 — HOLD 跳过 / 开仓 / 平仓 memory 关联 / position_pct 缩放

包含:
- TestTradeHold — HOLD 信号返回 None
- TestTradeExecute — BUY/SELL 执行交易
- TestTradeMemory — 平仓时更新记忆结果
- TestTradePositionPct — multi_agent 时按 position_pct 缩放
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.engine.result.signal import Signal


class TestTradeHold:
    """HOLD 信号跳过交易执行。"""

    @pytest.mark.asyncio
    async def test_hold_returns_none(self, mock_engine):
        """HOLD 信号不调用 trade.execute。"""
        sig = Signal(signal="HOLD")
        from app.engine.loop.tick_trade import tick_execute_trade
        result = await tick_execute_trade(mock_engine, sig, 100.0, None)
        assert result is None
        mock_engine.trade.execute.assert_not_called()


class TestTradeExecute:
    """正常交易执行。"""

    @pytest.mark.asyncio
    async def test_buy_executes_with_params(self, mock_engine):
        """BUY 信号调用 trade.execute 并传入正确参数。"""
        sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
        mock_engine.trade.execute = AsyncMock(return_value={"action": "open"})
        mock_engine.use_multi_agent = False

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            mock_rt.side_effect = lambda key: {"order_amount": 5.0, "leverage": 10}[key]
            from app.engine.loop.tick_trade import tick_execute_trade
            result = await tick_execute_trade(mock_engine, sig, 100.0, None)

        assert result == {"action": "open"}
        mock_engine.trade.execute.assert_called_once()
        call_kwargs = mock_engine.trade.execute.call_args.kwargs
        assert call_kwargs["signal"] == "BUY"
        assert call_kwargs["price"] == 100.0
        assert call_kwargs["stop_loss"] == 97.0
        assert call_kwargs["take_profit"] == 105.0
        assert call_kwargs["amount_usdt"] == 5.0
        assert call_kwargs["leverage"] == 10

    @pytest.mark.asyncio
    async def test_sell_executes(self, mock_engine):
        """SELL 信号正常执行。"""
        sig = Signal(signal="SELL", stop_loss=103.0, take_profit=95.0)
        mock_engine.trade.execute = AsyncMock(return_value={"action": "open"})
        mock_engine.use_multi_agent = False

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            mock_rt.side_effect = lambda key: {"order_amount": 3.0, "leverage": 5}[key]
            from app.engine.loop.tick_trade import tick_execute_trade
            result = await tick_execute_trade(mock_engine, sig, 200.0, None)

        assert result is not None
        call_kwargs = mock_engine.trade.execute.call_args.kwargs
        assert call_kwargs["signal"] == "SELL"


class TestTradeMemory:
    """平仓/反向时关联记忆结果。"""

    @pytest.mark.asyncio
    async def test_reverse_updates_memory_outcome(self, mock_engine):
        """反向交易时也更新记忆。"""
        sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
        mock_engine.trade.execute = AsyncMock(return_value={
            "action": "reverse", "pnl": -3.0,
        })
        mock_engine.use_multi_agent = False
        mock_engine._open_trade_memory_id = 3
        fake_memory = MagicMock()

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt, \
             patch("app.engine.loop.tick_trade.memory_service", fake_memory):
            mock_rt.side_effect = lambda key: {"order_amount": 1.0, "leverage": 10}[key]
            from app.engine.loop.tick_trade import tick_execute_trade
            await tick_execute_trade(mock_engine, sig, 100.0, None)

        fake_memory.update_outcome.assert_called_once_with(3, -3.0)
        assert mock_engine._open_trade_memory_id is None

    @pytest.mark.asyncio
    async def test_open_does_not_update_memory(self, mock_engine):
        """开仓(open)时不清除 memory_id。"""
        sig = Signal(signal="BUY", stop_loss=95.0, take_profit=105.0)
        mock_engine.trade.execute = AsyncMock(return_value={"action": "open"})
        mock_engine.use_multi_agent = False
        mock_engine._open_trade_memory_id = 5
        fake_memory = MagicMock()

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt, \
             patch("app.engine.loop.tick_trade.memory_service", fake_memory):
            mock_rt.side_effect = lambda key: {"order_amount": 1.0, "leverage": 10}[key]
            from app.engine.loop.tick_trade import tick_execute_trade
            await tick_execute_trade(mock_engine, sig, 100.0, None)

        fake_memory.update_outcome.assert_not_called()
        assert mock_engine._open_trade_memory_id == 5  # 保持不变

    @pytest.mark.asyncio
    async def test_add_does_not_update_memory(self, mock_engine):
        """加仓(add)时不清除 memory_id（TradeService 真实 action）。"""
        sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
        mock_engine.trade.execute = AsyncMock(return_value={"action": "add"})
        mock_engine.use_multi_agent = False
        mock_engine._open_trade_memory_id = 5
        fake_memory = MagicMock()

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt, \
             patch("app.engine.loop.tick_trade.memory_service", fake_memory):
            mock_rt.side_effect = lambda key: {"order_amount": 1.0, "leverage": 10}[key]
            from app.engine.loop.tick_trade import tick_execute_trade
            await tick_execute_trade(mock_engine, sig, 100.0, None)

        fake_memory.update_outcome.assert_not_called()
        assert mock_engine._open_trade_memory_id == 5


class TestTradePositionPct:
    """multi_agent 模式下按 position_pct 缩放金额。"""

    @pytest.mark.asyncio
    async def test_scales_by_position_pct(self, mock_engine):
        """multi_agent + decision 时 order_amount *= position_pct / 100。"""
        sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
        mock_engine.trade.execute = AsyncMock(return_value={"action": "open"})
        mock_engine.use_multi_agent = True

        decision = {"position_pct": 50}
        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            mock_rt.side_effect = lambda key: {"order_amount": 10.0, "leverage": 10}[key]
            from app.engine.loop.tick_trade import tick_execute_trade
            await tick_execute_trade(mock_engine, sig, 100.0, decision)

        call_kwargs = mock_engine.trade.execute.call_args.kwargs
        assert call_kwargs["amount_usdt"] == 5.0  # 10 * 50/100

    @pytest.mark.asyncio
    async def test_default_position_pct_100(self, mock_engine):
        """decision 无 position_pct 时默认 100。"""
        sig = Signal(signal="BUY", stop_loss=97.0, take_profit=105.0)
        mock_engine.trade.execute = AsyncMock(return_value={"action": "open"})
        mock_engine.use_multi_agent = True

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            mock_rt.side_effect = lambda key: {"order_amount": 8.0, "leverage": 10}[key]
            from app.engine.loop.tick_trade import tick_execute_trade
            await tick_execute_trade(mock_engine, sig, 100.0, {})

        call_kwargs = mock_engine.trade.execute.call_args.kwargs
        assert call_kwargs["amount_usdt"] == 8.0  # 8 * 100/100
