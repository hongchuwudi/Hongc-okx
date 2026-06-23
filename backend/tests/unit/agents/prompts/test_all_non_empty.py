"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_all_non_empty.py 提示词非空测试
描述: 验证 7 个 Agent 提示词常量都不是空字符串
"""

from app.agents.prompts.prompt_scheduler import SCHEDULER_PROMPT
from app.agents.prompts.prompt_analyst import ANALYST_PROMPT
from app.agents.prompts.prompt_reviewer import REVIEWER_PROMPT
from app.agents.prompts.prompt_risk import RISK_PROMPT
from app.agents.prompts.prompt_trader import TRADER_PROMPT
from app.agents.prompts.prompt_super_analyst import SUPER_ANALYST_PROMPT
from app.agents.prompts.prompt_solo import SOLO_PROMPT


def test_all_prompts_are_non_empty_strings():
    prompts = {
        "scheduler": SCHEDULER_PROMPT,
        "analyst": ANALYST_PROMPT,
        "reviewer": REVIEWER_PROMPT,
        "risk": RISK_PROMPT,
        "trader": TRADER_PROMPT,
        "super_analyst": SUPER_ANALYST_PROMPT,
        "solo": SOLO_PROMPT,
    }
    for name, prompt in prompts.items():
        assert isinstance(prompt, str), f"{name} 提示词不是字符串类型"
        assert prompt.strip(), f"{name} 提示词为空或仅含空白字符"
