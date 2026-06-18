"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: test_tick_strategy.py 策略分析测试
描述: 验证 AI 策略、技术指标策略、AI 失败降级三条路径

包含:
- TestStrategyAI — AI 正常产出的信号格式
- TestStrategyTech — tech 模式走技术指标
- TestStrategyDegrade — AI 失败时降级 + 连续失败计数
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestStrategyAI:
    """AI 多 Agent 模式正常产出信号。"""

    @pytest.mark.asyncio
    async def test_ai_returns_valid_signal(self, mock_engine, sample_df, sample_account):
        from app.engine.loop.tick_strategy import tick_analyze_strategy
        signal, decision = await tick_analyze_strategy(
            mock_engine, sample_df, 100.0, sample_account, None,
        )
        assert signal.signal == "BUY"
        assert signal.confidence == "HIGH"
        assert signal.stop_loss > 0
        assert signal.take_profit > signal.stop_loss

    @pytest.mark.asyncio
    async def test_ai_resets_fail_count_on_success(self, mock_engine, sample_df, sample_account):
        mock_engine._agent_fail_count = 3
        from app.engine.loop.tick_strategy import tick_analyze_strategy
        await tick_analyze_strategy(mock_engine, sample_df, 100.0, sample_account, None)
        assert mock_engine._agent_fail_count == 0


class TestStrategyTech:
    """纯技术指标模式。"""

    @pytest.mark.asyncio
    async def test_tech_mode_skips_ai(self, mock_engine, sample_df, sample_account):
        mock_engine.use_multi_agent = False
        from app.engine.loop.tick_strategy import tick_analyze_strategy
        signal, decision = await tick_analyze_strategy(
            mock_engine, sample_df, 100.0, sample_account, None,
        )
        assert decision is None
        assert signal.signal in ("BUY", "SELL", "HOLD")


class TestStrategyDegrade:
    """AI 调用失败时的降级行为。"""

    @pytest.mark.asyncio
    async def test_ai_failure_falls_back_to_tech(self, mock_engine, sample_df, sample_account):
        mock_engine.coordinator.analyze = AsyncMock(side_effect=Exception("API 超时"))
        from app.engine.loop.tick_strategy import tick_analyze_strategy
        signal, decision = await tick_analyze_strategy(
            mock_engine, sample_df, 100.0, sample_account, None,
        )
        assert mock_engine._agent_fail_count == 1
        assert "降级" in str(signal.agent_reports.get("degraded", ""))

    @pytest.mark.asyncio
    async def test_ai_consecutive_fail_count(self, mock_engine, sample_df, sample_account):
        mock_engine.coordinator.analyze = AsyncMock(side_effect=Exception("超时"))
        mock_engine._agent_fail_count = 4
        from app.engine.loop.tick_strategy import tick_analyze_strategy
        await tick_analyze_strategy(mock_engine, sample_df, 100.0, sample_account, None)
        # 第 5 次失败，fail_count 应为 5
        assert mock_engine._agent_fail_count == 5
