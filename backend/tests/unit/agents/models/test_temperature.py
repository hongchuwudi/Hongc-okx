"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_temperature.py 温度参数测试
描述: 验证各 Agent 模型的 temperature 值符合设计规范
"""

from unittest.mock import patch

from app.core.config import config as cfg

# 设计规范: (Agent, 温度, 说明)
_EXPECTED = [
    ("scheduler",      0.3,  "调度师-快速扫描"),
    ("analyst",        0.3,  "分析师-标准分析"),
    ("reviewer",       0.3,  "复盘师-经验提取"),
    ("risk",           0.1,  "风控师-确定性输出"),
    ("trader",         0.2,  "交易员-偏保守决策"),
    ("super_analyst",  0.3,  "超级分析师-综合分析"),
    ("solo",           0.15, "Solo-兼顾风控与分析"),
]


def test_temperature_values_match_design():
    """各 Agent 的 temperature 必须匹配设计值。"""
    _reset_all_singletons()
    with patch.object(cfg.ai, 'deepseek_api_key', 'test-key'):
        from app.agents.models.model_scheduler import get_scheduler_llm
        from app.agents.models.model_analyst import get_analyst_llm
        from app.agents.models.model_reviewer import get_reviewer_llm
        from app.agents.models.model_risk import get_risk_llm
        from app.agents.models.model_trader import get_trader_llm
        from app.agents.models.model_super_analyst import get_super_analyst_llm
        from app.agents.models.model_solo import get_solo_llm

        factories = {
            "scheduler": get_scheduler_llm, "analyst": get_analyst_llm,
            "reviewer": get_reviewer_llm, "risk": get_risk_llm,
            "trader": get_trader_llm, "super_analyst": get_super_analyst_llm,
            "solo": get_solo_llm,
        }
        for name, expected_temp, desc in _EXPECTED:
            llm = factories[name]()
            actual = llm.temperature
            assert actual == expected_temp, (
                f"{name}({desc}) temperature={actual}, 期望 {expected_temp}"
            )


def _reset_all_singletons():
    import sys
    modules = [f"app.agents.models.model_{n}" for n in
               ("scheduler","analyst","reviewer","risk","trader","super_analyst","solo")]
    for mod_name in modules:
        if mod_name in sys.modules:
            sys.modules[mod_name]._llm = None
