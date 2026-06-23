"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_ai_fallback.py AI 降级
描述: AI 失败时降级为技术指标
"""
import pytest
from unittest.mock import AsyncMock
@pytest.mark.asyncio
async def test_ai_failure_falls_back(mock_engine, sample_df, sample_account):
    mock_engine.coordinator.analyze = AsyncMock(side_effect=Exception("API timeout"))
    from app.engine.loop.tick_strategy import tick_analyze_strategy
    signal, decision = await tick_analyze_strategy(mock_engine, sample_df, 100.0, sample_account, None)
    assert mock_engine._agent_fail_count == 1
    assert "降级" in str(signal.agent_reports.get("degraded",""))
