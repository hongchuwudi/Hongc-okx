"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_defines_role.py 提示词角色定义测试
描述: 验证每个 Agent 提示词第一句明确说明了角色身份
"""

from app.agents.prompts import PROMPT_DEFAULTS

# 每个 Agent 的角色关键词
_ROLE_KEYWORDS = {
    "scheduler": "调度师",
    "analyst": "分析师",
    "reviewer": "复盘师",
    "risk": "风控师",
    "trader": "裁决员",
    "super_analyst": "超级分析师",
    "solo": "全能交易员",
}


def test_every_prompt_defines_agent_role():
    """每个提示词的第一句必须定义角色身份。"""
    for name, (default, label) in PROMPT_DEFAULTS.items():
        first_line = default.strip().split("。")[0].split("。")[0].split("\n")[0].strip()
        keyword = _ROLE_KEYWORDS.get(name, "")
        assert keyword, f"{label}({name}) 未配置角色关键词"
        assert keyword in first_line, (
            f"{label}({name}) 首行未声明角色 '{keyword}': {first_line[:50]}..."
        )
