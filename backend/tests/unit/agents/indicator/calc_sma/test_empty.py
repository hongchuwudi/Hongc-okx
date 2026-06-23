"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_empty.py SMA 空数据测试
描述: 空 DataFrame 验证返回含 "无数据"
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_sma


def test_sma_empty_data(empty_df):
    assert "无数据" in calc_sma(20)
