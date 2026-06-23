"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_real_kline.py RSI 真实行情测试
描述: 用 data/kline/demo/doge/doge_1m_*.csv 真实 DOGE K 线数据，
     验证 calc_rsi(14) 返回值在 0-100 之间且标签正确

验证点:
- RSI 数值在 [0, 100] 区间
- 标签为 超买(>70) / 超卖(<30) / 中性 三者之一
- 标签与数值区间一致
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_rsi


def test_rsi_with_real_doge_kline(real_kline):
    result = calc_rsi(14)
    # RSI(14): 45.2 — 中性
    match = re.search(r"RSI\(14\):\s*([\d.]+|nan)\s*—\s*(.+)", result)
    assert match is not None, f"输出格式不符合预期: {result}"

    rsi_str, label = match.group(1), match.group(2)
    assert rsi_str != "nan", f"RSI 不应为 NaN (真实行情有涨有跌): {result}"

    rsi_val = float(rsi_str)
    assert 0 <= rsi_val <= 100, f"RSI 超出 [0,100]: {rsi_val}"

    valid_labels = {"超买", "超卖", "中性"}
    assert label in valid_labels, f"标签异常: {label}"

    if rsi_val > 70:
        assert label == "超买", f"RSI={rsi_val} > 70 应为超买, 实际 {label}"
    elif rsi_val < 30:
        assert label == "超卖", f"RSI={rsi_val} < 30 应为超卖, 实际 {label}"
    else:
        assert label == "中性", f"RSI={rsi_val} 在 30-70 应为中性, 实际 {label}"
