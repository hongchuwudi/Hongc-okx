"""
测试: Solo Agent 解析失败时兜底返回 HOLD
"""

import pytest
from contextlib import ExitStack
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_solo_fallback_on_parse_failure(sample_df):
    """LLM 返回无法解析的文本时，兜底返回 HOLD。"""
    from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo

    with patch.object(AgentCoordinatorSolo, '__init__', lambda self: None):
        coordinator = AgentCoordinatorSolo.__new__(AgentCoordinatorSolo)
        coordinator._agent = MagicMock()
        coordinator._llm = MagicMock()
        coordinator._logger = MagicMock()
        coordinator._cfg = {}

        # 两次都返回无效文本
        fake_result = MagicMock()
        fake_result.__getitem__ = lambda s, k: [MagicMock(content="无效输出")] if k == "messages" else MagicMock()
        coordinator._agent.invoke = MagicMock(return_value=fake_result)
        coordinator._llm.invoke = MagicMock(return_value=MagicMock(content="还是无效"))

        async def fake_thread(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        with ExitStack() as stack:
            for ctx in [
                patch('app.agents.coordinators.coordinator_solo.asyncio.to_thread', fake_thread),
                patch('app.agents.coordinators.coordinator_solo.load_data'),
                patch('app.agents.coordinators.coordinator_solo.generate_feedback', return_value=""),
                patch('app.agents.coordinators.coordinator_solo.last_content', return_value="无效输出"),
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
                result = await coordinator.analyze(sample_df, 100.0, 10000.0, None)

    assert result["signal"] == "HOLD"
    assert result["source_count"] == 1
