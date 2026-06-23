"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_schema_fields.py 提示词 JSON 字段完整性测试
描述: 验证每个 Agent 提示词要求的 JSON 字段列表完整
"""

from app.agents.prompts import PROMPT_DEFAULTS

# 每个 Agent 必须包含的关键 JSON 字段
_REQUIRED_FIELDS = {
    "scheduler": ["focus", "priority", "summary"],
    "analyst": ["signal", "confidence", "trend_direction", "trend_strength", "report", "key_evidence"],
    "reviewer": ["lesson", "recent_win_rate", "warning", "suggestion"],
    "risk": ["go_no_go", "max_position_pct", "sl_boundary_pct", "tp_boundary_pct", "risk_rating", "risk_assessment"],
    "trader": ["signal", "confidence", "position_pct", "stop_loss", "take_profit", "reason", "key_factor"],
    "super_analyst": ["focus", "signal", "confidence", "report", "lesson", "suggestion"],
    "solo": ["signal", "confidence", "position_pct", "stop_loss", "take_profit", "reason", "risk_rating"],
}


def test_each_prompt_contains_required_json_fields():
    """每个提示词规定的 JSON 字段必须完整。"""
    for name, (default, label) in PROMPT_DEFAULTS.items():
        required = _REQUIRED_FIELDS.get(name, [])
        assert required, f"{label}({name}) 未配置必填字段列表"
        for field in required:
            assert f'"{field}"' in default or f"'{field}'" in default or field in default, (
                f"{label}({name}) 提示词缺少字段 '{field}'"
            )
