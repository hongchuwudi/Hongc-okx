"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty.py 布林带空数据测试
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_bollinger


def test_bollinger_empty_data(empty_df):
    assert calc_bollinger() == "布林带: 无数据"
