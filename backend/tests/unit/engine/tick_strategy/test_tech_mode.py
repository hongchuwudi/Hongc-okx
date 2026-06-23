"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_tech_mode.py 技术指标模式
描述: tech 模式跳过 AI，decision=None
"""
import pytest
@pytest.mark.asyncio
async def test_tech_mode_skips_ai(mock_engine, sample_df, sample_account):
    mock_engine.use_multi_agent = False
    from app.engine.loop.tick_strategy import tick_analyze_strategy
    signal, decision = await tick_analyze_strategy(mock_engine, sample_df, 100.0, sample_account, None)
    assert decision is None and signal.signal in ("BUY","SELL","HOLD")
