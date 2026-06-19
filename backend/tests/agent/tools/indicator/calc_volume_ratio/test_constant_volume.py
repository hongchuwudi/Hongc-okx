"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_constant_volume.py 量比恒定成交量测试
描述: 恒定 volume=1000 → 量比 ≈ 1.0，标签为"正常"
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_volume_ratio


def test_volume_ratio_constant_volume_is_normal(constant_vol_df):
    result = calc_volume_ratio(20)
    match = re.search(r"量比:\s*([\d.]+)", result)
    assert match is not None, f"无法提取量比值: {result}"
    ratio = float(match.group(1))
    assert abs(ratio - 1.0) < 0.1, f"恒定成交量量比应 ≈ 1.0, 实际 {ratio}"
    assert "正常" in result
