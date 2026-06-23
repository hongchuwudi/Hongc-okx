"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_returns_chatopenai.py 模型工厂返回值测试
描述: 验证全部 7 个模型工厂返回 ChatOpenAI 实例
"""

from unittest.mock import patch
from langchain_openai import ChatOpenAI

from app.core.config import config as cfg


def test_all_factories_return_chatopenai():
    """全部 7 个模型工厂必须返回 ChatOpenAI 实例。"""
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
        for name, factory in factories.items():
            llm = factory()
            assert isinstance(llm, ChatOpenAI), (
                f"{name} 工厂返回 {type(llm).__name__}, 期望 ChatOpenAI"
            )


def _reset_all_singletons():
    import sys
    modules = [f"app.agents.models.model_{n}" for n in
               ("scheduler","analyst","reviewer","risk","trader","super_analyst","solo")]
    for mod_name in modules:
        if mod_name in sys.modules:
            sys.modules[mod_name]._llm = None
