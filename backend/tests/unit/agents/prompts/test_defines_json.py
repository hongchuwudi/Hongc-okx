"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_defines_json.py 提示词 JSON 格式测试
描述: 验证每个 Agent 提示词都规定了 JSON 输出格式
"""

from app.agents.prompts import PROMPT_DEFAULTS


def test_every_prompt_defines_json_output_format():
    """每个提示词必须包含 JSON 输出格式说明（"输出 JSON" 或花括号模式）。"""
    for name, (default, label) in PROMPT_DEFAULTS.items():
        has_json = "{" in default and "}" in default
        has_keyword = "输出 JSON" in default or "输出合并 JSON" in default
        assert has_json or has_keyword, (
            f"{label}({name}) 提示词缺少 JSON 输出格式定义"
        )
