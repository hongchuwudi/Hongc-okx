"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_ai_valid_signal.py AI 合法信号
描述: AI 多 Agent 产出合法 Signal
"""
import pytest
@pytest.mark.asyncio
async def test_ai_returns_valid_signal(mock_engine, sample_df, sample_account):
    from app.engine.loop.tick_strategy import tick_analyze_strategy
    signal, decision = await tick_analyze_strategy(mock_engine, sample_df, 100.0, sample_account, None)
    assert signal.signal == "BUY" and signal.confidence == "HIGH"
    assert signal.stop_loss > 0 and signal.take_profit > signal.stop_loss
