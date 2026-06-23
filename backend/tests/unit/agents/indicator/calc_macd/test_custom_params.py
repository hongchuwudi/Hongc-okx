"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_custom_params.py MACD 自定义参数测试
描述: 用非默认参数 (fast=6, slow=13, signal=5) 验证 MACD 正常工作
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import calc_macd


def test_macd_custom_params_works(uptrend_df):
    result = calc_macd(fast=6, slow=13, signal=5)
    assert "MACD" in result
    assert "信号" in result
    assert "柱" in result
