"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_risk_go_no_go.py 风控师 go_no_go 测试
描述: 验证风控师提示词包含 go_no_go 门禁和风控边界字段
"""

from app.agents.prompts.prompt_risk import RISK_PROMPT


def test_risk_prompt_has_go_no_go_gate():
    """风控师提示词必须包含 go_no_go 硬门禁。"""
    assert "go_no_go" in RISK_PROMPT, "缺少 go_no_go 字段定义"
    assert "GO" in RISK_PROMPT, "缺少 GO 枚举值"
    assert "NO_GO" in RISK_PROMPT, "缺少 NO_GO 枚举值"
    assert "宁可错过不可做错" in RISK_PROMPT, "缺少风控核心原则"


def test_risk_prompt_has_boundary_fields():
    """风控师提示词必须包含止盈止损边界字段。"""
    assert "sl_boundary_pct" in RISK_PROMPT, "缺少止损边界字段"
    assert "tp_boundary_pct" in RISK_PROMPT, "缺少止盈边界字段"
    assert "max_position_pct" in RISK_PROMPT, "缺少最大仓位字段"
    assert "risk_rating" in RISK_PROMPT, "缺少风险评级字段"
