"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_uptrend.py 趋势上涨测试
描述: 构造纯涨序列，验证整体趋势为 bullish
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_trend


def test_trend_uptrend_is_bullish(uptrend_df):
    result = calc_trend()
    # 纯涨趋势整体应为 bullish
    assert "bullish" in result, f"纯涨趋势整体应为 bullish: {result[:80]}"
