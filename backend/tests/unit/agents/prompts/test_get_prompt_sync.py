"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_get_prompt_sync.py get_prompt_sync 函数测试
描述: 验证 get_prompt_sync 对全部 7 个 Agent 返回非空字符串
"""

from app.agents.prompts import PROMPT_DEFAULTS, get_prompt_sync


def test_get_prompt_sync_returns_string_for_all_agents():
    """get_prompt_sync 对每个已注册 name 返回非空字符串。"""
    for name in PROMPT_DEFAULTS:
        result = get_prompt_sync(name)
        assert isinstance(result, str), f"get_prompt_sync({name}) 返回类型 {type(result)}"
        assert result.strip(), f"get_prompt_sync({name}) 返回空字符串"


def test_get_prompt_sync_unknown_returns_fallback():
    """未知 name 返回空字符串拼接后缀。"""
    result = get_prompt_sync("nonexistent_agent")
    assert isinstance(result, str), f"未知 name 应返回字符串，实际 {type(result)}"
