"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: test_tick_flow.py 完整流程集成测试
描述: Mock 全部外部服务（含 DB/Redis），验证 _tick 从开始到完成全流程

包含:
- TestTickFlow — 完整 8 步流程 + HOLD 信号跳过交易 + 熔断跳过
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _build_engine(mock_engine):
    """用 mock_engine 属性构建真实 TradingEngine 实例。"""
    from app.engine.engine import TradingEngine
    with patch.object(TradingEngine, '__init__', lambda self: None):
        engine = TradingEngine.__new__(TradingEngine)
        for attr in dir(mock_engine):
            if not attr.startswith('_'):
                try:
                    setattr(engine, attr, getattr(mock_engine, attr))
                except (TypeError, AttributeError):
                    pass
        for attr in ['_symbol', '_probe_count', '_agent_fail_count',
                     '_open_trade_memory_id', '_last_mode', '_last_symbol',
                     '_last_leverage', '_last_prompt_version']:
            setattr(engine, attr, getattr(mock_engine, attr))
        engine.use_multi_agent = mock_engine.use_multi_agent
        engine.agent_mode_display = mock_engine.agent_mode_display
        engine.exchange = mock_engine.exchange
        engine.market_data = mock_engine.market_data
        engine.risk = mock_engine.risk
        engine.trade = mock_engine.trade
        engine.strategy_service = mock_engine.strategy_service
        engine.coordinator = mock_engine.coordinator
        engine.position_manager = mock_engine.position_manager
        engine.scheduler = mock_engine.scheduler
        engine._sync_runtime = AsyncMock()
        return engine


class TestTickFlow:
    """验证 _tick() 编排的完整流程。"""

    @pytest.mark.asyncio
    async def test_full_tick_completes(self, mock_engine):
        """正常 tick：8 步全部执行，不报错。"""
        with patch('app.engine.engine.tick_record_memory', AsyncMock()), \
             patch('app.engine.engine.tick_persist_and_notify', AsyncMock()):
            engine = _build_engine(mock_engine)
            await engine._tick()

            engine.market_data.get_ohlcv.assert_called_once()
            engine.coordinator.analyze.assert_called_once()
            engine.risk.check.assert_called_once()

    @pytest.mark.asyncio
    async def test_tick_skips_on_circuit_paused(self, mock_engine):
        """熔断暂停时直接 return，不调用行情获取。"""
        mock_engine.risk.check_pause = AsyncMock(return_value={
            "resumed": False, "blocked": True, "remaining_s": 60
        })
        from app.engine.engine import TradingEngine
        with patch.object(TradingEngine, '__init__', lambda self: None):
            engine = TradingEngine.__new__(TradingEngine)
            engine.risk = mock_engine.risk
            await engine._tick()
            mock_engine.market_data.get_ohlcv.assert_not_called()

    @pytest.mark.asyncio
    async def test_tick_hold_skips_trade(self, mock_engine):
        """HOLD 信号不执行交易。"""
        mock_engine.coordinator.analyze = AsyncMock(return_value={
            "signal": "HOLD", "confidence": "LOW", "reason": "观望",
            "stop_loss": 98.0, "take_profit": 102.0,
            "source_count": 5, "agent_reports": {}, "position_pct": 0,
        })
        with patch('app.engine.engine.tick_record_memory', AsyncMock()), \
             patch('app.engine.engine.tick_persist_and_notify', AsyncMock()):
            engine = _build_engine(mock_engine)
            await engine._tick()
            engine.trade.execute.assert_not_called()
