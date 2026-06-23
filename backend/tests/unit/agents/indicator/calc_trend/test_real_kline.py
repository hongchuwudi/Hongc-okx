"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_real_kline.py 趋势真实行情测试
描述: 用真实 DOGE 1m K 线验证 calc_trend() 输出含短期/中期/整体三段

输出格式: 趋势 短期:bullish/bearish/neutral | 中期:bullish/bearish/neutral | 整体:bullish/bearish/震荡/分歧
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_trend


def test_trend_with_real_doge_kline(real_kline):
    result = calc_trend()
    assert result.startswith("趋势")
    assert "短期:" in result
    assert "中期:" in result
    assert "整体:" in result
    # 整体必须包含三种判定之一
    valid_overall = {"bullish", "bearish", "震荡/分歧"}
    found = [v for v in valid_overall if v in result]
    assert len(found) >= 1, f"整体趋势缺失: {result}"
