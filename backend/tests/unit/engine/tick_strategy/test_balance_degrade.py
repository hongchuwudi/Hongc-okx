"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_balance_degrade.py AI 余额不足降级
描述: DeepSeek 余额 < 0.05 时，tick_strategy 降级为技术指标，不走 agent

覆盖:
- 余额不足 → 走技术指标，coordinator.analyze 不被调用，decision 为 None
- 余额充足 → 走 agent 路线，coordinator.analyze 被调用
- 余额查询失败 → 容错不阻断，仍走 agent 路线（让 AI 自身失败降级兜底）
- 降级仅本 tick 跳过，不改 engine.use_multi_agent 标志
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.engine.loop.tick_strategy import tick_analyze_strategy


# 注意：本目录 conftest 的 autouse fixture 默认 mock 余额充足。
# 本文件测降级，需在每个用例里自行 patch 余额检查返回值。

@pytest.mark.asyncio
async def test_balance_insufficient_degrades_to_technical(mock_engine, sample_df, sample_account):
    """余额不足时，走技术指标，coordinator 不被调用。"""
    mock_engine.coordinator.analyze = AsyncMock(return_value={
        "signal": "BUY", "confidence": "HIGH", "reason": "不应被调用",
        "stop_loss": 98, "take_profit": 102, "source_count": 5, "agent_reports": {},
    })

    with patch(
        "app.services.agent.agent_balance_service.check_balance_sufficient",
        new=AsyncMock(return_value=(False, -0.1)),
    ):
        signal, decision = await tick_analyze_strategy(
            mock_engine, sample_df, 100.0, sample_account, None
        )

    # coordinator 绝不应被调用
    mock_engine.coordinator.analyze.assert_not_called()
    # decision 应为 None（降级不产生 agent decision）
    assert decision is None
    # 走了技术指标：agent_reports 标记降级来源
    assert "degraded" in signal.agent_reports
    assert "余额" in signal.agent_reports["degraded"]
    # use_multi_agent 标志不应被改动（仅本 tick 跳过）
    assert mock_engine.use_multi_agent is True


@pytest.mark.asyncio
async def test_balance_sufficient_goes_agent(mock_engine, sample_df, sample_account):
    """余额充足时，走 agent 路线，coordinator 被调用。"""
    mock_engine.coordinator.analyze = AsyncMock(return_value={
        "signal": "BUY", "confidence": "HIGH", "reason": "agent 决策",
        "stop_loss": 98, "take_profit": 102, "source_count": 5, "agent_reports": {"a": "ok"},
    })

    with patch(
        "app.services.agent.agent_balance_service.check_balance_sufficient",
        new=AsyncMock(return_value=(True, 50.0)),
    ):
        signal, decision = await tick_analyze_strategy(
            mock_engine, sample_df, 100.0, sample_account, None
        )

    mock_engine.coordinator.analyze.assert_called_once()
    assert decision is not None
    assert signal.signal == "BUY"
    assert signal.source_count == 5


@pytest.mark.asyncio
async def test_balance_query_failure_does_not_degrade(mock_engine, sample_df, sample_account):
    """余额查询失败时，容错不阻断，仍走 agent 路线（让 AI 失败降级兜底）。"""
    mock_engine.coordinator.analyze = AsyncMock(return_value={
        "signal": "HOLD", "confidence": "LOW", "reason": "agent 正常",
        "stop_loss": 98, "take_profit": 102, "source_count": 5, "agent_reports": {},
    })

    with patch(
        "app.services.agent.agent_balance_service.check_balance_sufficient",
        new=AsyncMock(return_value=(True, -1.0)),  # 查询失败返回 sufficient=True
    ):
        signal, decision = await tick_analyze_strategy(
            mock_engine, sample_df, 100.0, sample_account, None
        )

    # 查询失败不降级，agent 被调用
    mock_engine.coordinator.analyze.assert_called_once()
    assert decision is not None


@pytest.mark.asyncio
async def test_balance_insufficient_does_not_increment_fail_count(mock_engine, sample_df, sample_account):
    """余额不足降级不应累加 AI 失败计数（与 AI 调用失败降级区分）。"""
    mock_engine._agent_fail_count = 0
    mock_engine.coordinator.analyze = AsyncMock()

    with patch(
        "app.services.agent.agent_balance_service.check_balance_sufficient",
        new=AsyncMock(return_value=(False, -0.1)),
    ):
        await tick_analyze_strategy(mock_engine, sample_df, 100.0, sample_account, None)

    # 余额降级不是 AI 调用失败，fail_count 不应增加
    assert mock_engine._agent_fail_count == 0
