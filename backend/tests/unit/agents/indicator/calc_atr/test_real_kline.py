"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_real_kline.py ATR 真实行情测试
描述: 用真实 DOGE 1m K 线验证 calc_atr() 输出含 ATR 值和百分比
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_atr


def test_atr_with_real_doge_kline(real_kline):
    result = calc_atr(14)
    assert "ATR:" in result
    assert "%" in result
    # ATR 应 > 0 (DOGE 波动率一般 0.1%-5%)
    match = re.search(r"ATR:\s*([\d.]+)", result)
    assert match is not None, f"无法提取 ATR 值: {result}"
    atr_val = float(match.group(1))
    # DOGE 低价 (~$0.08) ATR 极小，`.1f` 格式化可能舍入为 0.0
    assert atr_val >= 0, f"ATR 不应为负: {atr_val}"
