"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty.py MACD 空数据测试
描述: 空 DataFrame 输入时验证返回 "MACD: 无数据"
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_macd


def test_macd_empty_data(empty_df):
    assert calc_macd() == "MACD: 无数据"
