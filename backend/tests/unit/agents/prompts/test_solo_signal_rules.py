"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_solo_signal_rules.py Solo 信号规则测试
描述: 验证 Solo 提示词包含 6 条明确的交易信号判断规则
"""

from app.agents.prompts.prompt_solo import SOLO_PROMPT


def test_solo_prompt_has_six_signal_rules():
    """Solo 提示词必须包含 RSI/SMA/布林带共 6 条交易信号规则。"""
    assert "RSI < 30" in SOLO_PROMPT, "缺少 RSI 超卖规则"
    assert "RSI > 70" in SOLO_PROMPT, "缺少 RSI 超买规则"
    assert "金叉" in SOLO_PROMPT or "SMA5" in SOLO_PROMPT, "缺少 SMA 金叉规则"
    assert "死叉" in SOLO_PROMPT, "缺少 SMA 死叉规则"
    assert "布林带下轨" in SOLO_PROMPT, "缺少布林带下轨规则"
    assert "布林带上轨" in SOLO_PROMPT, "缺少布林带上轨规则"
