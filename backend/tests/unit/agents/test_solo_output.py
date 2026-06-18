"""
测试: 1 Agent Solo analyze() 输出格式（Mock LLM）
"""

import pytest
from contextlib import ExitStack
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_analyze_returns_required_keys(sample_df):
    """analyze() 返回 dict 必须包含 signal/confidence/reason/stop_loss/take_profit。"""
    result = await _run_solo(sample_df)
    required = {"signal", "confidence", "reason", "stop_loss", "take_profit", "position_pct", "source_count", "agent_reports"}
    missing = required - set(result.keys())
    assert not missing, f"缺少字段: {missing}"


@pytest.mark.asyncio
async def test_analyze_signal_is_valid(sample_df):
    """返回的 signal 必须是 BUY/SELL/HOLD。"""
    result = await _run_solo(sample_df)
    assert result["signal"] in ("BUY", "SELL", "HOLD")


@pytest.mark.asyncio
async def test_analyze_buy_has_sl_below_tp(sample_df):
    """BUY 信号 stop_loss < take_profit。"""
    result = await _run_solo(sample_df, signal="BUY")
    if result["signal"] == "BUY":
        assert result["stop_loss"] < result["take_profit"]


@pytest.mark.asyncio
async def test_source_count_is_one(sample_df):
    """Solo 模式 source_count 固定为 1。"""
    result = await _run_solo(sample_df)
    assert result["source_count"] == 1


async def _run_solo(sample_df, signal="BUY"):
    """Mock LLM 后调用 Solo coordinator.analyze()。"""
    from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo

    with patch.object(AgentCoordinatorSolo, '__init__', lambda self: None):
        coordinator = AgentCoordinatorSolo.__new__(AgentCoordinatorSolo)
        coordinator._agent = MagicMock()
        coordinator._llm = MagicMock()
        coordinator._logger = MagicMock()
        coordinator._cfg = {}

        raw = f'{{"signal": "{signal}", "confidence": "HIGH", "reason": "mock", "stop_loss": 97.0, "take_profit": 105.0, "position_pct": 50, "risk_rating": "MEDIUM"}}'
        fake_result = MagicMock()
        fake_result.__getitem__ = lambda s, k: [MagicMock(content=raw)] if k == "messages" else MagicMock()
        coordinator._agent.invoke = MagicMock(return_value=fake_result)

        async def fake_thread(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        with ExitStack() as stack:
            for ctx in [
                patch('app.agents.coordinators.coordinator_solo.asyncio.to_thread', fake_thread),
                patch('app.agents.coordinators.coordinator_solo.load_data'),
                patch('app.agents.coordinators.coordinator_solo.generate_feedback', return_value=""),
                patch('app.agents.coordinators.coordinator_solo.last_content', return_value=raw),
                patch('app.agents.coordinators.coordinator_solo.IndicatorService'),
                patch('app.agents.coordinators.coordinator_solo.evaluate_position_risk'),
                patch('app.agents.coordinators.coordinator_solo.calc_max_position'),
                patch('app.agents.coordinators.coordinator_solo.calc_sl_tp'),
                patch('app.agents.coordinators.coordinator_solo.get_runtime', return_value=10),
                patch('app.agents.coordinators.coordinator_solo.agent_input', AsyncMock()),
                patch('app.agents.coordinators.coordinator_solo.agent_output', AsyncMock()),
                patch('app.agents.coordinators.coordinator_solo.set_current_agent'),
                patch('app.agents.coordinators.coordinator_solo.ToolCallLogger'),
            ]:
                stack.enter_context(ctx)

            with patch.object(coordinator, '_base', return_value={"messages": [MagicMock()], "remaining_steps": 6, "price": 100.0, "equity": 10000.0}), \
                 patch.object(coordinator, '_empty', return_value={"signal": "", "confidence": "", "reason": "", "position_pct": 0, "stop_loss": 0, "take_profit": 0, "risk_rating": "", "final_decision": {}}):
                return await coordinator.analyze(sample_df, 100.0, 10000.0, None)
