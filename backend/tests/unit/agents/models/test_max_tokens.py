"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_max_tokens.py max_tokens 测试
描述: 验证各 Agent 模型的 max_tokens 值符合设计规范
"""

from unittest.mock import patch

from app.core.config import config as cfg

# 设计规范: (Agent, max_tokens, 说明)
_EXPECTED = [
    ("scheduler",      300,   "调度师-轻量JSON"),
    ("analyst",        800,   "分析师-完整报告"),
    ("reviewer",       500,   "复盘师-简短教训"),
    ("risk",           600,   "风控师-边界计算"),
    ("trader",         2000,  "交易员-完整决策链"),
    ("super_analyst",  1200,  "超级分析师-合并输出"),
    ("solo",           1500,  "Solo-全流程决策"),
]


def test_max_tokens_values_match_design():
    """各 Agent 的 max_tokens 必须匹配设计值。"""
    # 重置所有模型的全局单例，注入假 API Key
    with patch.object(cfg.ai, 'deepseek_api_key', 'test-key'):
        _reset_all_singletons()

        from app.agents.models.model_scheduler import get_scheduler_llm
        from app.agents.models.model_analyst import get_analyst_llm
        from app.agents.models.model_reviewer import get_reviewer_llm
        from app.agents.models.model_risk import get_risk_llm
        from app.agents.models.model_trader import get_trader_llm
        from app.agents.models.model_super_analyst import get_super_analyst_llm
        from app.agents.models.model_solo import get_solo_llm

        factories = {
            "scheduler": get_scheduler_llm,
            "analyst": get_analyst_llm,
            "reviewer": get_reviewer_llm,
            "risk": get_risk_llm,
            "trader": get_trader_llm,
            "super_analyst": get_super_analyst_llm,
            "solo": get_solo_llm,
        }
        for name, expected_tokens, desc in _EXPECTED:
            llm = factories[name]()
            actual = llm.max_tokens
            assert actual == expected_tokens, (
                f"{name}({desc}) max_tokens={actual}, 期望 {expected_tokens}"
            )


def _reset_all_singletons():
    """重置所有模型模块的 _llm 全局单例。"""
    modules = [
        "app.agents.models.model_scheduler",
        "app.agents.models.model_analyst",
        "app.agents.models.model_reviewer",
        "app.agents.models.model_risk",
        "app.agents.models.model_trader",
        "app.agents.models.model_super_analyst",
        "app.agents.models.model_solo",
    ]
    import importlib, sys
    for mod_name in modules:
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            if hasattr(mod, '_llm'):
                mod._llm = None
