"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_fixed_tr.py ATR 固定 TR 收敛测试
描述: 构造 TR 恒为 2.0 的 K 线 (high=close+1, low=close-1, 无 gap)，
     验证 ATR(14) 收敛到约 2.0

计算: TR = max(high-low, |high-prev_close|, |low-prev_close|)
          = max(2.0, |(prev_close+1+1)-prev_close|, |(prev_close+1-1)-prev_close|)
          = max(2.0, 2.0, 0.0) = 2.0
      EWM(alpha=1/14) 收敛后 ATR ≈ 2.0
"""

import re
from app.agents.toolkits.tools.toolkit_calc_indicator import calc_atr


def test_atr_converges_to_fixed_true_range(fixed_tr_df):
    result = calc_atr(14)
    match = re.search(r"ATR:\s*([\d.]+)", result)
    assert match is not None, f"无法提取 ATR 值: {result}"
    atr_val = float(match.group(1))
    # EWM 从第一根 K 线开始收敛，30 根后应在 2.0 ± 0.5 内
    assert 1.5 <= atr_val <= 2.5, f"ATR 应收敛到 2.0, 实际 {atr_val}"
