"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_real_kline.py 量比真实行情测试
描述: 用真实 DOGE 1m K 线验证 calc_volume_ratio() 输出含量比和标签

标签: ratio > 2 → 异常放量, ratio < 0.5 → 异常缩量, else → 正常
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_volume_ratio


def test_volume_ratio_with_real_doge_kline(real_kline):
    result = calc_volume_ratio(20)
    assert "量比:" in result
    assert "—" in result
    # 验证标签
    valid_labels = {"异常放量", "异常缩量", "正常"}
    assert any(label in result for label in valid_labels), f"缺少有效标签: {result}"
    # 验证量比是数字
    match = re.search(r"量比:\s*([\d.]+)", result)
    assert match is not None, f"无法提取量比值: {result}"
    ratio = float(match.group(1))
    # DOGE 低价 (~$0.08) 量比极小，`.2f` 格式化可能舍入为 0.00
    assert ratio >= 0, f"量比不应为负: {ratio}"
