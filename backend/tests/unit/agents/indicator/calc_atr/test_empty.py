"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty.py ATR 空数据测试
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_atr


def test_atr_empty_data(empty_df):
    assert calc_atr() == "ATR: 无数据"
