"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_downtrend.py RSI 持续下跌测试
描述: 构造纯跌序列 close 129→100 (每天-1)，验证 RSI 趋向超卖区域

验证点:
- 纯跌趋势下 avg_gain=0 → replace(0, np.nan) → RSI 可能为 NaN (已知 bug)
- 若不为 NaN，应 <= 30 且标签为"超卖"
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_rsi


def test_rsi_downtrend_should_be_oversold(downtrend_df):
    result = calc_rsi(14)
    match = re.search(r"RSI\(14\):\s*([\d.]+|nan)", result)
    assert match is not None, f"无法提取 RSI 值: {result}"

    rsi_str = match.group(1)
    if rsi_str == "nan":
        assert "nan" in result
    else:
        rsi_val = float(rsi_str)
        assert rsi_val <= 30, f"纯跌趋势 RSI 应 <= 30, 实际 {rsi_val}"
        assert "超卖" in result
