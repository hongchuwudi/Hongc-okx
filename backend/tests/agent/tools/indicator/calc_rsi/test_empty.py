"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty.py RSI 空数据测试
描述: 空 DataFrame 输入时验证返回 "RSI: 无数据" 而不崩溃
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_rsi


def test_rsi_empty_data_returns_no_data(empty_df):
    assert calc_rsi(14) == "RSI: 无数据"
