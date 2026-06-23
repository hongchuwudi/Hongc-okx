"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_solo_hold_last.py Solo HOLD 最后选择测试
描述: 验证 Solo 提示词明确 HOLD 是最后选项
"""

from app.agents.prompts.prompt_solo import SOLO_PROMPT


def test_solo_prompt_hold_is_last_resort():
    """Solo 提示词必须明确 HOLD 是最后选择而非默认选项。"""
    assert "HOLD" in SOLO_PROMPT, "Solo 提示词未提及 HOLD"
    # HOLD 应该是最后选择
    has_hold_last = (
        "HOLD 是最后选择" in SOLO_PROMPT
        or "HOLD是最后选择" in SOLO_PROMPT
        or "最后选择" in SOLO_PROMPT
        or "不是默认选择" in SOLO_PROMPT
    )
    assert has_hold_last, "Solo 提示词未明确 HOLD 是最后选择"
