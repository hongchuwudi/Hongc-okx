"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_uptrend.py 布林带上涨趋势测试
描述: 纯涨趋势下价格应接近上轨，价格位置 > 50%
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_bollinger


def test_bollinger_uptrend_price_near_upper_band(uptrend_df):
    result = calc_bollinger()
    match = re.search(r"价格位置:([\d.]+)%", result)
    assert match is not None, f"缺少价格位置: {result}"
    pos = float(match.group(1))
    assert pos > 50, f"上涨趋势价格位置应 > 50%, 实际 {pos}%"
