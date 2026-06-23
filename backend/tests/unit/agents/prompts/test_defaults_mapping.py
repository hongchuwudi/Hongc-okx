"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_defaults_mapping.py PROMPT_DEFAULTS 映射测试
描述: 验证 PROMPT_DEFAULTS 覆盖全部 7 个 Agent 且标签正确
"""

from app.agents.prompts import PROMPT_DEFAULTS

_EXPECTED_AGENTS = {
    "scheduler": "调度师",
    "analyst": "分析师",
    "reviewer": "复盘师",
    "risk": "风控师",
    "trader": "交易员",
    "super_analyst": "超级分析师",
    "solo": "Solo",
}


def test_prompt_defaults_covers_all_seven_agents():
    """PROMPT_DEFAULTS 必须包含全部 7 个 Agent。"""
    assert len(PROMPT_DEFAULTS) == 7, f"期望 7 个 Agent, 实际 {len(PROMPT_DEFAULTS)}"
    for name, (default, label) in PROMPT_DEFAULTS.items():
        assert name in _EXPECTED_AGENTS, f"未知 Agent: {name}"
        assert label == _EXPECTED_AGENTS[name], (
            f"{name} 标签期望 '{_EXPECTED_AGENTS[name]}', 实际 '{label}'"
        )
        assert isinstance(default, str) and default.strip(), (
            f"{name} 默认提示词为空"
        )
