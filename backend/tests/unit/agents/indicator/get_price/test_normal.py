"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_normal.py 当前价格测试
描述: 加载真实 DOGE 1m K 线后验证 get_price() 返回格式正确

输出格式: 当前价格: $0.08362
"""

from app.agents.toolkits.tools.toolkit_calc_indicator import get_price


def test_get_price_with_real_kline(real_kline):
    result = get_price()
    assert result.startswith("当前价格: $"), f"价格格式错误: {result}"
