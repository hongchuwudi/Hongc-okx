"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty.py 趋势空数据测试
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_trend


def test_trend_empty_data(empty_df):
    assert calc_trend() == "趋势: 无数据"
