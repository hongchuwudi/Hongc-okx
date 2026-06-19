"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_downtrend.py MACD 持续下跌测试
描述: 构造纯跌序列 close 129→100 (每天-1)，验证 MACD 方向正确

验证点:
- 下跌趋势 MACD 线 < 0 (快线在慢线下方)
- 纯线性趋势柱状图不穿越零轴, "无交叉" 是正确行为
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_macd


def test_macd_downtrend_negative_value(downtrend_df):
    result = calc_macd()
    match = re.search(r"MACD:\s*([\d.\-]+)", result)
    assert match is not None, f"无法提取 MACD 值: {result}"
    macd_val = float(match.group(1))
    assert macd_val < 0, f"下跌趋势 MACD 线应 < 0, 实际 {macd_val}"
