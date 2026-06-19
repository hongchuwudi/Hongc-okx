"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_real_kline.py SMA 真实行情测试
描述: 用真实 DOGE 1m K 线验证 calc_sma(20) 输出含 SMA 值和价格偏离百分比
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_sma


def test_sma20_with_real_doge_kline(real_kline):
    result = calc_sma(20)
    assert "SMA20:" in result
    assert "价格偏离" in result
    # 验证偏离百分比存在
    match = re.search(r"价格偏离([+-][\d.]+)%", result)
    assert match is not None, f"缺少价格偏离百分比: {result}"
