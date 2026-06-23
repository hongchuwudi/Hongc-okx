"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_suffix_appended.py 提示词后缀测试
描述: 验证 get_prompt_sync 返回值包含通用学习后缀 _H
"""

from app.agents.prompts import get_prompt_sync


def test_prompt_suffix_contains_memory_instructions():
    """所有 Agent 提示词必须追加通用记忆学习后缀。"""
    # 使用 scheduler 作为代表（所有 prompt 通过 get_prompt_sync 都会追加 _H）
    prompt = get_prompt_sync("scheduler")
    assert "check_my_accuracy" in prompt, (
        "提示词未包含 check_my_accuracy 工具说明"
    )
    assert "remember" in prompt, (
        "提示词未包含 remember 工具说明"
    )
    assert "result" in prompt.lower(), (
        "提示词未包含 result 反馈记录说明"
    )
