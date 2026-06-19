"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_insufficient.py SMA 数据不足测试
描述: 3 行 K 线求 SMA50 → 返回 "数据不足"
"""

import pandas as pd
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_sma


def test_sma50_insufficient_data():
    from app.agents.toolkits.toolkit_data import load_data
    tiny = pd.DataFrame({"close": [100.0, 101.0, 102.0]})
    load_data(tiny, 102.0, 10000.0)
    result = calc_sma(50)
    assert "数据不足" in result
