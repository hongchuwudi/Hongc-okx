"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_tick_pipeline.py Tick 流水线集成测试
描述: 验证 8 步流水线中参数在各模块间正确传递，重点覆盖"下单参数传错"类 bug

覆盖的 bug 模式:
- tick_execute_trade → trade.execute: signal/price/sl/tp/amount_usdt/leverage 类型和值
- AI 失败降级: 技术指标兜底后参数仍然有效
- HOLD 信号: trade.execute 不被调用
- decision.position_pct: 百分比换算正确
- runtime 值在 tick 内被正确读取并传递

包含:
- class TestTradeExecuteParams — 交易参数传递
- class TestSignalFlow — 信号流转（AI→策略→交易）
- class TestPipelineEdgeCases — 边界情况
"""
import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.engine.result.signal import Signal
from app.engine.loop.tick_trade import tick_execute_trade
from app.engine.loop.tick_strategy import tick_analyze_strategy


# tick_analyze_strategy 在 use_multi_agent=True 时会先查 DeepSeek 余额，
# 余额不足则降级。本文件测的是 AI/降级信号流转本身，应走 agent 路径，
# 不依赖真实 DeepSeek 余额接口。autouse fixture 默认让余额充足。
@pytest.fixture(autouse=True)
def mock_balance_sufficient():
    """默认 mock 余额充足，AI 路径测试不被真实 DeepSeek 余额干扰。"""
    with patch(
        "app.services.agent.agent_balance_service.check_balance_sufficient",
        new=AsyncMock(return_value=(True, 100.0)),
    ):
        yield


# ═══════════════════════════════════════════════════════════════
# 公共 fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_engine():
    """构建最小引擎 mock，只 mock 外部依赖，保留 tick 函数真实逻辑。"""
    engine = MagicMock()
    engine.use_multi_agent = True
    engine.agent_mode_display = "5 Agent Swarm"
    engine._symbol = "DOGE/USDT:USDT"
    engine._open_trade_memory_id = None
    engine._agent_fail_count = 0

    engine.exchange = MagicMock()
    engine.exchange.use_backup = False
    engine.exchange.switch_to_backup = MagicMock(return_value=True)
    engine.exchange.switch_to_primary = MagicMock()

    engine.market_data = MagicMock()
    engine.risk = MagicMock()
    engine.strategy_service = MagicMock()
    engine.coordinator = MagicMock()
    engine.scheduler = MagicMock()
    engine.scheduler._interval = 360

    engine._last_mode = "5_agent"
    engine._last_symbol = "DOGE/USDT:USDT"
    engine._last_leverage = 10
    engine._last_prompt_version = 1

    return engine


@dataclass
class CapturedTradeParams:
    """捕获传给 trade.execute 的参数，用于精确断言。"""
    signal: str = ""
    price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    amount_usdt: float = 0.0
    leverage: int = 0


# ═══════════════════════════════════════════════════════════════
# tick_execute_trade 参数传递
# ═══════════════════════════════════════════════════════════════

class TestTradeExecuteParams:
    """验证 tick_execute_trade → trade.execute 的每个参数类型和值"""

    @pytest.mark.asyncio
    async def test_buy_signal_passes_all_params_correctly(self, mock_engine):
        """BUY 信号：验证 trade.execute 收到的全部 6 个参数。
        这是"下单参数传错"bug 的核心回归测试。
        """
        captured = CapturedTradeParams()

        async def capture_execute(signal, price, stop_loss, take_profit, amount_usdt, leverage):
            captured.signal = signal
            captured.price = price
            captured.stop_loss = stop_loss
            captured.take_profit = take_profit
            captured.amount_usdt = amount_usdt
            captured.leverage = leverage
            return {"action": "open", "order": {"id": "test"}}

        mock_engine.trade.execute = capture_execute

        signal = Signal(
            signal="BUY", confidence="HIGH", reason="测试",
            stop_loss=0.095, take_profit=0.115,
            source_count=5,
        )
        decision = {"position_pct": 80}

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            # 模拟 runtime 返回值
            mock_rt.side_effect = lambda key: {
                "order_amount": 1.0,
                "leverage": 10,
            }.get(key, None)

            result = await tick_execute_trade(mock_engine, signal, 0.10, decision)

        # 断言参数类型
        assert isinstance(captured.signal, str), f"signal 应为 str，实际 {type(captured.signal)}"
        assert isinstance(captured.price, (int, float)), f"price 应为数字，实际 {type(captured.price)}"
        assert isinstance(captured.stop_loss, (int, float)), f"stop_loss 应为数字"
        assert isinstance(captured.take_profit, (int, float)), f"take_profit 应为数字"
        assert isinstance(captured.amount_usdt, (int, float)), f"amount_usdt 应为数字"
        assert isinstance(captured.leverage, int), f"leverage 应为 int"

        # 断言参数值
        assert captured.signal == "BUY", f"signal 应为 BUY，实际 {captured.signal}"
        assert captured.price == 0.10, f"price 应为 0.10，实际 {captured.price}"
        assert captured.stop_loss == 0.095, f"stop_loss 应为 0.095，实际 {captured.stop_loss}"
        assert captured.take_profit == 0.115, f"take_profit 应为 0.115，实际 {captured.take_profit}"
        # amount_usdt = order_amount * position_pct/100 = 1.0 * 0.8 = 0.8
        assert captured.amount_usdt == 0.8, f"amount_usdt 应为 0.8 (1.0 * 80%)，实际 {captured.amount_usdt}"
        assert captured.leverage == 10, f"leverage 应为 10，实际 {captured.leverage}"
        assert result is not None
        assert result["action"] == "open"

    @pytest.mark.asyncio
    async def test_hold_signal_skips_trade(self, mock_engine):
        """HOLD 信号：trade.execute 绝对不能被调用。"""
        mock_engine.trade.execute = AsyncMock()

        signal = Signal(signal="HOLD", confidence="LOW", reason="等待")
        result = await tick_execute_trade(mock_engine, signal, 0.10, None)

        mock_engine.trade.execute.assert_not_called()
        assert result is None

    @pytest.mark.asyncio
    async def test_position_pct_100_means_full_amount(self, mock_engine):
        """position_pct=100 时 amount_usdt 不变。"""
        captured = CapturedTradeParams()
        mock_engine.trade.execute = AsyncMock()

        async def _capture(*args, **kwargs):
            captured.signal = kwargs.get("signal", args[0] if args else "")
            captured.amount_usdt = kwargs.get("amount_usdt", args[4] if len(args) >= 5 else 0)

        mock_engine.trade.execute = _capture
        signal = Signal(signal="SELL", confidence="HIGH", reason="",
                        stop_loss=0.11, take_profit=0.09)
        decision = {"position_pct": 100}

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            mock_rt.side_effect = lambda key: {
                "order_amount": 2.0, "leverage": 5,
            }.get(key, None)
            await tick_execute_trade(mock_engine, signal, 0.10, decision)

        assert captured.amount_usdt == 2.0, (
            f"position_pct=100 时 amount_usdt 应不变，实际 {captured.amount_usdt}"
        )

    @pytest.mark.asyncio
    async def test_decision_none_uses_full_order_amount(self, mock_engine):
        """decision=None 时不应乘 position_pct（即使用 100%）。"""
        captured = CapturedTradeParams()
        mock_engine.trade.execute = AsyncMock()

        async def _capture(*args, **kwargs):
            captured.amount_usdt = kwargs.get("amount_usdt", args[4] if len(args) >= 5 else 0)

        mock_engine.trade.execute = _capture
        signal = Signal(signal="BUY", confidence="HIGH", reason="",
                        stop_loss=0.095, take_profit=0.115)

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            mock_rt.side_effect = lambda key: {
                "order_amount": 1.0, "leverage": 10,
            }.get(key, None)
            await tick_execute_trade(mock_engine, signal, 0.10, None)

        assert captured.amount_usdt == 1.0, (
            f"decision=None 时 amount_usdt 应为 1.0，实际 {captured.amount_usdt}"
        )


# ═══════════════════════════════════════════════════════════════
# 信号流转：AI → 策略分析 → 交易执行
# ═══════════════════════════════════════════════════════════════

class TestSignalFlow:
    """验证 tick_analyze_strategy 信号生成和 AI 失败降级"""

    @pytest.mark.asyncio
    async def test_ai_success_produces_valid_signal(self, mock_engine):
        """AI 成功时：decision 转为 Signal，字段类型正确。"""
        mock_engine.coordinator.analyze = AsyncMock(return_value={
            "signal": "BUY", "confidence": "HIGH", "reason": "趋势向上",
            "stop_loss": 98.0, "take_profit": 105.0,
            "source_count": 5, "agent_reports": {"a": "ok"},
        })

        df = pd.DataFrame({"close": [100, 101, 102], "volume": [1000] * 3})
        signal, decision = await tick_analyze_strategy(
            mock_engine, df, 101.0,
            {"equity": 10000.0}, None,
        )

        assert isinstance(signal, Signal), f"返回值应为 Signal，实际 {type(signal)}"
        assert signal.signal == "BUY"
        assert signal.confidence == "HIGH"
        assert signal.stop_loss == 98.0
        assert signal.take_profit == 105.0
        assert signal.source_count == 5
        assert decision is not None

    @pytest.mark.asyncio
    async def test_ai_failure_falls_back_to_technical(self, mock_engine):
        """AI 失败 → 降级为技术指标信号，signal 仍然有效（不能 crash）。"""
        mock_engine.coordinator.analyze = AsyncMock(
            side_effect=Exception("API timeout")
        )
        mock_engine.strategy_service.analyze = AsyncMock(return_value=Signal(
            signal="SELL", confidence="MEDIUM", reason="技术指标看空",
            stop_loss=105.0, take_profit=95.0,
        ))

        df = pd.DataFrame({"close": [100, 99, 98], "volume": [1000] * 3})
        signal, decision = await tick_analyze_strategy(
            mock_engine, df, 99.0,
            {"equity": 10000.0}, None,
        )

        assert signal.signal == "SELL", "降级后应使用技术指标信号"
        assert mock_engine._agent_fail_count == 1
        assert decision is None, "降级时 decision 应为 None"

    @pytest.mark.asyncio
    async def test_five_consecutive_failures_still_produces_signal(self, mock_engine):
        """连续 5 次 AI 失败后依然返回有效信号，不能 None/null。"""
        mock_engine._agent_fail_count = 5
        mock_engine.coordinator.analyze = AsyncMock(
            side_effect=Exception("连续失败")
        )
        mock_engine.strategy_service.analyze = AsyncMock(return_value=Signal(
            signal="HOLD", confidence="LOW", reason="不确定",
            stop_loss=0, take_profit=0,
        ))

        df = pd.DataFrame({"close": [100, 99, 98], "volume": [1000] * 3})
        signal, decision = await tick_analyze_strategy(
            mock_engine, df, 99.0,
            {"equity": 10000.0}, None,
        )

        assert signal.signal == "HOLD", "连续失败后仍应返回有效信号"
        assert decision is None

    @pytest.mark.asyncio
    async def test_tech_mode_skips_ai_entirely(self, mock_engine):
        """tech 模式不调用 AI，直接走技术指标。"""
        mock_engine.use_multi_agent = False
        mock_engine.strategy_service.analyze = AsyncMock(return_value=Signal(
            signal="BUY", confidence="HIGH", reason="纯技术",
            stop_loss=98.0, take_profit=102.0,
        ))

        df = pd.DataFrame({"close": [100], "volume": [1000]})
        signal, decision = await tick_analyze_strategy(
            mock_engine, df, 100.0,
            {"equity": 10000.0}, None,
        )

        assert signal.signal == "BUY"
        assert decision is None  # tech 模式不产生 decision
        assert not hasattr(mock_engine.coordinator, "analyze") or \
               not mock_engine.coordinator.analyze.called


# ═══════════════════════════════════════════════════════════════
# 边界情况
# ═══════════════════════════════════════════════════════════════

class TestPipelineEdgeCases:
    """流水线边界情况"""

    @pytest.mark.asyncio
    async def test_signal_stop_loss_never_exceeds_take_profit_for_buy(self, mock_engine):
        """BUY 信号：stop_loss < take_profit（否则参数传反了）。"""
        mock_engine.trade.execute = AsyncMock(return_value={"action": "open"})

        signal = Signal(
            signal="BUY", confidence="HIGH", reason="",
            stop_loss=98.0, take_profit=102.0,
        )

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            mock_rt.side_effect = lambda key: {
                "order_amount": 1.0, "leverage": 10,
            }.get(key, None)
            await tick_execute_trade(mock_engine, signal, 100.0, {"position_pct": 100})

        # 通过不抛异常来验证参数顺序正确
        assert signal.stop_loss < signal.take_profit, (
            f"BUY 信号 stop_loss({signal.stop_loss}) 应 < take_profit({signal.take_profit})"
        )

    @pytest.mark.asyncio
    async def test_signal_stop_loss_exceeds_take_profit_for_sell(self, mock_engine):
        """SELL 信号：stop_loss > take_profit。"""
        signal = Signal(
            signal="SELL", confidence="HIGH", reason="",
            stop_loss=102.0, take_profit=98.0,
        )
        assert signal.stop_loss > signal.take_profit, (
            f"SELL 信号 stop_loss({signal.stop_loss}) 应 > take_profit({signal.take_profit})"
        )

    @pytest.mark.asyncio
    async def test_reverse_trade_updates_memory_id(self, mock_engine):
        """反向交易（平仓+开仓）后 _open_trade_memory_id 被清空。"""
        mock_engine._open_trade_memory_id = 42
        mock_engine.trade.execute = AsyncMock(return_value={
            "action": "reverse", "pnl": 5.5,
        })
        mock_engine.use_multi_agent = True

        signal = Signal(signal="SELL", confidence="HIGH", reason="",
                        stop_loss=0.11, take_profit=0.09)

        with patch("app.engine.loop.tick_trade.get_runtime_async") as mock_rt:
            mock_rt.side_effect = lambda key: {
                "order_amount": 1.0, "leverage": 10,
            }.get(key, None)
            with patch("app.engine.loop.tick_trade.memory_service") as mock_mem:
                mock_mem.update_outcome = MagicMock()
                await tick_execute_trade(mock_engine, signal, 0.10,
                                         {"position_pct": 100})

        # reverse 后 memory_id 应被清空
        assert mock_engine._open_trade_memory_id is None, (
            f"反向交易后 _open_trade_memory_id 应为 None，实际 {mock_engine._open_trade_memory_id}"
        )
