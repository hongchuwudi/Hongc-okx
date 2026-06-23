"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_trader_risk_override.py 交易员风控覆盖测试
描述: 验证交易员提示词包含风控 NO_GO 强制 HOLD 约束
"""

from app.agents.prompts.prompt_trader import TRADER_PROMPT


def test_trader_prompt_respects_risk_no_go():
    """交易员提示词必须声明风控 NO_GO 时必须 HOLD。"""
    assert "NO_GO" in TRADER_PROMPT, "交易员提示词未提及风控 NO_GO"
    has_override = "NO_GO" in TRADER_PROMPT and "HOLD" in TRADER_PROMPT
    assert has_override, "交易员提示词未声明风控 NO_GO 时输出 HOLD"
    assert "综合团队意见" in TRADER_PROMPT or "风控" in TRADER_PROMPT, (
        "交易员提示词未提及综合风控意见"
    )
