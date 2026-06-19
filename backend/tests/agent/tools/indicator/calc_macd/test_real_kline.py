"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_real_kline.py MACD 真实行情测试
描述: 用真实 DOGE 1m K 线验证 calc_macd() 输出结构完整

验证点:
- 输出包含 MACD 线值 / 信号线值 / 柱状图值
- 交叉状态为 金叉/死叉/无交叉 之一
- 柱状图为扩大或收缩
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_macd


def test_macd_with_real_doge_kline(real_kline):
    result = calc_macd()
    # MACD: 0.00012 | 信号: 0.00010 | 柱: 0.00002(扩大) | 金叉 ↑
    assert "MACD:" in result
    assert "信号:" in result
    assert "柱:" in result

    # 验证交叉状态
    valid_cross = {"金叉", "死叉", "无交叉"}
    found = [c for c in valid_cross if c in result]
    assert len(found) == 1, f"应有且仅有一个交叉状态, 实际: {found}, output={result[:100]}"

    # 验证柱状图方向
    assert "扩大" in result or "收缩" in result
