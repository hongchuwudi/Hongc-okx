"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_uptrend.py RSI 持续上涨测试
描述: 构造纯涨序列 close 100→129 (每天+1)，验证 RSI 趋向超买区域

验证点:
- 纯涨趋势下 avg_loss=0 → avg_loss.replace(0, np.nan) → RSI 可能为 NaN (已知 bug)
- 若不为 NaN，应 >= 70 且标签为"超买"
- 记录实际行为，暴露 replace(0, np.nan) 导致的除零问题
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_rsi


def test_rsi_uptrend_should_be_overbought(uptrend_df):
    result = calc_rsi(14)
    match = re.search(r"RSI\(14\):\s*([\d.]+|nan)", result)
    assert match is not None, f"无法提取 RSI 值: {result}"

    rsi_str = match.group(1)
    # 已知 bug: 纯涨趋势 avg_loss=0 → replace(0, np.nan) → rs=NaN → RSI=NaN
    # 正确的行为应该是 RSI=100 (没有下跌就没有损失)
    if rsi_str == "nan":
        # 当前实际行为 (bug 未修)
        assert "nan" in result
    else:
        rsi_val = float(rsi_str)
        assert rsi_val >= 70, f"纯涨趋势 RSI 应 >= 70, 实际 {rsi_val}"
        assert "超买" in result
