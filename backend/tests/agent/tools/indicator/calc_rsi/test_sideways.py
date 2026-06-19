"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_sideways.py RSI 横盘震荡测试
描述: 构造横盘序列 close 恒为 100 (±0.01 噪声)，验证 RSI 在 50 附近且标签为"中性"

验证点:
- 横盘时涨跌幅度相近，avg_gain ≈ avg_loss，RSI 应在 40-60 之间
- 标签为"中性"
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_rsi


def test_rsi_sideways_should_be_neutral(sideways_df):
    result = calc_rsi(14)
    match = re.search(r"RSI\(14\):\s*([\d.]+|nan)\s*—\s*(.+)", result)
    assert match is not None, f"无法解析 RSI 输出: {result}"

    rsi_str, label = match.group(1), match.group(2)
    assert rsi_str != "nan", f"横盘有微小涨跌不应为 NaN: {result}"

    rsi_val = float(rsi_str)
    assert 40 <= rsi_val <= 60, f"横盘 RS I应在 40-60, 实际 {rsi_val}"
    assert label == "中性", f"横盘标签应为中性, 实际 {label}"
