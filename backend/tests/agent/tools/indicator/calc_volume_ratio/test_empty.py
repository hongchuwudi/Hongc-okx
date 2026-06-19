"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty.py 量比空数据测试
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_volume_ratio


def test_volume_ratio_empty_data(empty_df):
    assert calc_volume_ratio() == "量比: 无数据"
