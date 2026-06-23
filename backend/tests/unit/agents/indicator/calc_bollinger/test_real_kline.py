"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_real_kline.py 布林带真实行情测试
描述: 用真实 DOGE 1m K 线验证 calc_bollinger() 输出含上/中/下轨 + 价格位置 + 带宽
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_bollinger


def test_bollinger_with_real_doge_kline(real_kline):
    result = calc_bollinger()
    assert "布林带:" in result
    assert "上" in result and "中" in result and "下" in result
    assert "价格位置" in result
    assert "带宽" in result
    # 价格位置应是一个百分比
    match = re.search(r"价格位置:([\d.]+)%", result)
    assert match is not None, f"缺少价格位置: {result}"
    pos = float(match.group(1))
    assert 0 <= pos <= 100, f"价格位置应在 0-100%, 实际 {pos}%"
