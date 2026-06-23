"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_singleton.py 模型单例测试
描述: 验证同一工厂多次调用返回同一实例
"""

from unittest.mock import patch

from app.core.config import config as cfg


def test_all_factories_return_same_instance():
    """同一工厂两次调用必须返回同一实例（单例模式）。"""
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
            a = factory()
            b = factory()
            assert a is b, f"{name} 工厂未实现单例: {id(a)} != {id(b)}"


def _reset_all_singletons():
    import sys
    modules = [f"app.agents.models.model_{n}" for n in
               ("scheduler","analyst","reviewer","risk","trader","super_analyst","solo")]
    for mod_name in modules:
        if mod_name in sys.modules:
            sys.modules[mod_name]._llm = None
