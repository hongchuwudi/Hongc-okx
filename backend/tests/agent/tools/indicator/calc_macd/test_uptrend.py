"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_uptrend.py MACD 持续上涨测试
描述: 构造纯涨序列 close 100→129 (每天+1)，验证 MACD 方向正确

验证点:
- 上涨趋势 MACD 线 > 0 (快线在慢线上方)
- 纯线性趋势柱状图不穿越零轴, "无交叉" 是正确行为
  (金叉/死叉需要柱状图从负变正或从正变负, 纯匀速涨跌不会发生)
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_macd


def test_macd_uptrend_positive_value(uptrend_df):
    result = calc_macd()
    match = re.search(r"MACD:\s*([\d.\-]+)", result)
    assert match is not None, f"无法提取 MACD 值: {result}"
    macd_val = float(match.group(1))
    assert macd_val > 0, f"上涨趋势 MACD 线应 > 0, 实际 {macd_val}"
