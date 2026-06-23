"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_ai_resets_fail.py 失败计数重置
描述: AI 成功调用后 _agent_fail_count 归零
"""
import pytest
@pytest.mark.asyncio
async def test_ai_resets_fail_count(mock_engine, sample_df, sample_account):
    mock_engine._agent_fail_count = 3
    from app.engine.loop.tick_strategy import tick_analyze_strategy
    await tick_analyze_strategy(mock_engine, sample_df, 100.0, sample_account, None)
    assert mock_engine._agent_fail_count == 0
