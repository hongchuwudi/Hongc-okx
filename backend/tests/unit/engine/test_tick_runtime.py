"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_tick_runtime.py 运行时热切换测试
描述: 验证 5 个运行时模块的热切换行为

包含:
- TestRuntimeAgentMode — Agent 模式切换 (tech/1_agent/3_agent/5_agent)
- TestRuntimeLeverage — 杠杆切换 (有/无持仓)
- TestRuntimeSymbol — 交易对切换 (有/无持仓)
- TestRuntimeInterval — Tick 间隔切换
- TestRuntimePrompt — 提示词版本热重载
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ═══════════════════════════════════════════════════════════════
# Step 1a: Agent 模式热切换
# ═══════════════════════════════════════════════════════════════

class TestRuntimeAgentMode:

    @pytest.mark.asyncio
    async def test_switch_to_tech_disables_ai(self, mock_engine):
        """切换到 tech 模式：关闭 AI，coordinator 置空。"""
        mock_engine._last_mode = "5_agent"
        with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async",
                   AsyncMock(return_value="tech")):
            from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
            await _sync_agent_mode(mock_engine)

        assert mock_engine.use_multi_agent is False
        assert mock_engine.coordinator is None
        assert "技术指标" in mock_engine.agent_mode_display

    @pytest.mark.asyncio
    async def test_switch_to_1_agent(self, mock_engine):
        """切换到 1_agent 模式。"""
        mock_engine._last_mode = "tech"
        mock_engine.coordinator = None
        fake_coordinator = MagicMock()
        with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async",
                   AsyncMock(return_value="1_agent")), \
             patch("app.engine.runtime.runtime_agent_mode.create_coordinator_solo",
                   return_value=fake_coordinator):
            from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
            await _sync_agent_mode(mock_engine)

        assert mock_engine.use_multi_agent is True
        assert mock_engine.coordinator is fake_coordinator
        assert "1 Agent" in mock_engine.agent_mode_display

    @pytest.mark.asyncio
    async def test_switch_to_3_agent(self, mock_engine):
        """切换到 3_agent 模式。"""
        mock_engine._last_mode = "1_agent"
        fake_coordinator = MagicMock()
        with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async",
                   AsyncMock(return_value="3_agent")), \
             patch("app.engine.runtime.runtime_agent_mode.create_coordinator_3",
                   return_value=fake_coordinator):
            from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
            await _sync_agent_mode(mock_engine)

        assert mock_engine.use_multi_agent is True
        assert "3 Agent" in mock_engine.agent_mode_display

    @pytest.mark.asyncio
    async def test_switch_to_5_agent(self, mock_engine):
        """切换到 5_agent 模式（默认）。"""
        mock_engine._last_mode = "1_agent"
        fake_coordinator = MagicMock()
        with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async",
                   AsyncMock(return_value="5_agent")), \
             patch("app.engine.runtime.runtime_agent_mode.create_coordinator",
                   return_value=fake_coordinator):
            from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
            await _sync_agent_mode(mock_engine)

        assert mock_engine.use_multi_agent is True
        assert "5 Agent" in mock_engine.agent_mode_display

    @pytest.mark.asyncio
    async def test_noop_when_mode_unchanged(self, mock_engine):
        """模式未变化时跳过切换，coordinator 保持不变。"""
        mock_engine._last_mode = "5_agent"
        old_coordinator = mock_engine.coordinator
        with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async",
                   AsyncMock(return_value="5_agent")):
            from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
            await _sync_agent_mode(mock_engine)

        assert mock_engine.coordinator is old_coordinator


# ═══════════════════════════════════════════════════════════════
# Step 1b: 杠杆热切换
# ═══════════════════════════════════════════════════════════════

class TestRuntimeLeverage:

    @pytest.mark.asyncio
    async def test_noop_when_unchanged(self, mock_engine):
        """杠杆未变化时跳过。"""
        mock_engine._last_leverage = 10
        with patch("app.engine.runtime.runtime_leverage.get_runtime_async",
                   AsyncMock(return_value=10)):
            from app.engine.runtime.runtime_leverage import _sync_leverage
            await _sync_leverage(mock_engine)

        mock_engine.exchange.set_leverage.assert_not_called()

    @pytest.mark.asyncio
    async def test_apply_when_no_position(self, mock_engine):
        """无持仓时直接切换杠杆。"""
        mock_engine._last_leverage = 5
        mock_engine.market_data.get_positions = AsyncMock(return_value=None)
        with patch("app.engine.runtime.runtime_leverage.get_runtime_async",
                   AsyncMock(return_value=20)):
            from app.engine.runtime.runtime_leverage import _sync_leverage
            await _sync_leverage(mock_engine)

        assert mock_engine._last_leverage == 20
        mock_engine.exchange.set_leverage.assert_called_once_with(
            mock_engine._symbol, 20
        )

    @pytest.mark.asyncio
    async def test_postpone_when_has_position(self, mock_engine):
        """有持仓时暂缓切换杠杆。"""
        mock_engine._last_leverage = 5
        mock_engine.market_data.get_positions = AsyncMock(return_value={
            "side": "long", "size": 0.1,
        })
        with patch("app.engine.runtime.runtime_leverage.get_runtime_async",
                   AsyncMock(return_value=20)):
            from app.engine.runtime.runtime_leverage import _sync_leverage
            await _sync_leverage(mock_engine)

        assert mock_engine._last_leverage == 20  # 记录已更新
        mock_engine.exchange.set_leverage.assert_not_called()  # 但未调用 API


# ═══════════════════════════════════════════════════════════════
# Step 1c: 交易对热切换
# ═══════════════════════════════════════════════════════════════

class TestRuntimeSymbol:

    @pytest.mark.asyncio
    async def test_noop_when_unchanged(self, mock_engine):
        """交易对未变化时跳过。"""
        mock_engine._last_symbol = "DOGE/USDT:USDT"
        mock_engine._symbol = "DOGE/USDT:USDT"
        with patch("app.engine.runtime.runtime_symbol.get_runtime_async",
                   AsyncMock(return_value="DOGE/USDT:USDT")):
            from app.engine.runtime.runtime_symbol import _sync_symbol
            await _sync_symbol(mock_engine)

        assert mock_engine._symbol == "DOGE/USDT:USDT"

    @pytest.mark.asyncio
    async def test_apply_when_no_position(self, mock_engine):
        """无持仓时直接切换交易对。"""
        mock_engine._last_symbol = "DOGE/USDT:USDT"
        mock_engine._symbol = "DOGE/USDT:USDT"
        mock_engine.market_data.get_positions = AsyncMock(return_value=None)
        with patch("app.engine.runtime.runtime_symbol.get_runtime_async",
                   AsyncMock(return_value="ETH/USDT:USDT")):
            from app.engine.runtime.runtime_symbol import _sync_symbol
            await _sync_symbol(mock_engine)

        assert mock_engine._symbol == "ETH/USDT:USDT"
        assert mock_engine.position_manager is not None

    @pytest.mark.asyncio
    async def test_postpone_when_has_position(self, mock_engine):
        """有持仓时暂缓切换交易对。"""
        original_symbol = "DOGE/USDT:USDT"
        mock_engine._last_symbol = original_symbol
        mock_engine._symbol = original_symbol
        mock_engine.market_data.get_positions = AsyncMock(return_value={
            "side": "long", "size": 0.1,
        })
        with patch("app.engine.runtime.runtime_symbol.get_runtime_async",
                   AsyncMock(return_value="ETH/USDT:USDT")):
            from app.engine.runtime.runtime_symbol import _sync_symbol
            await _sync_symbol(mock_engine)

        # 有持仓时 symbol 不变
        assert mock_engine._symbol == original_symbol


# ═══════════════════════════════════════════════════════════════
# Step 1d: Tick 间隔热切换
# ═══════════════════════════════════════════════════════════════

class TestRuntimeInterval:

    @pytest.mark.asyncio
    async def test_interval_updated(self, mock_engine):
        """间隔变化时更新调度器。"""
        mock_engine.scheduler._interval = 360
        with patch("app.engine.runtime.runtime_interval.get_runtime_async",
                   AsyncMock(return_value=60)):
            from app.engine.runtime.runtime_interval import _sync_interval
            await _sync_interval(mock_engine)

        assert mock_engine.scheduler._interval == 60

    @pytest.mark.asyncio
    async def test_noop_when_unchanged(self, mock_engine):
        """间隔未变化时跳过。"""
        mock_engine.scheduler._interval = 120
        with patch("app.engine.runtime.runtime_interval.get_runtime_async",
                   AsyncMock(return_value=120)):
            from app.engine.runtime.runtime_interval import _sync_interval
            await _sync_interval(mock_engine)

        assert mock_engine.scheduler._interval == 120


# ═══════════════════════════════════════════════════════════════
# Step 1e: 提示词热重载
# ═══════════════════════════════════════════════════════════════

class TestRuntimePrompt:

    @pytest.mark.asyncio
    async def test_prompt_version_change_rebuilds_coordinator(self, mock_engine):
        """提示词版本变化时重建 coordinator。"""
        mock_engine.use_multi_agent = True
        mock_engine.coordinator = MagicMock()
        mock_engine._last_prompt_version = 1
        mock_engine._last_mode = "5_agent"
        old_coordinator = mock_engine.coordinator
        fake_coordinator = MagicMock()

        with patch("app.agents.prompts.get_prompt_version",
                   AsyncMock(return_value=2)), \
             patch("app.services.agent.agent_coordinator_service.create_coordinator",
                   return_value=fake_coordinator):
            from app.engine.runtime.runtime_prompt import _sync_prompt
            await _sync_prompt(mock_engine)

        assert mock_engine._last_prompt_version == 2
        assert mock_engine.coordinator is fake_coordinator  # 已重建

    @pytest.mark.asyncio
    async def test_noop_when_not_multi_agent(self, mock_engine):
        """非 multi_agent 模式时跳过提示词同步。"""
        mock_engine.use_multi_agent = False
        mock_engine._last_prompt_version = 1

        from app.engine.runtime.runtime_prompt import _sync_prompt
        await _sync_prompt(mock_engine)

        # 未变化
        assert mock_engine._last_prompt_version == 1

    @pytest.mark.asyncio
    async def test_noop_when_version_unchanged(self, mock_engine):
        """提示词版本未变时不重建。"""
        mock_engine.use_multi_agent = True
        mock_engine.coordinator = MagicMock()
        mock_engine._last_prompt_version = 1
        old_coordinator = mock_engine.coordinator

        with patch("app.agents.prompts.get_prompt_version",
                   AsyncMock(return_value=1)):
            from app.engine.runtime.runtime_prompt import _sync_prompt
            await _sync_prompt(mock_engine)

        assert mock_engine.coordinator is old_coordinator
