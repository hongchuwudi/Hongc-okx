"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_model_name.py 模型名称测试
描述: 验证全部 Agent 使用正确的底层模型名称
"""

from unittest.mock import patch

from app.core.config import config as cfg


def test_all_models_use_deepseek_v4_flash():
    """全部 Agent 模型名必须为 deepseek-v4-flash。"""
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
            assert llm.model_name == "deepseek-v4-flash", (
                f"{name} model_name='{llm.model_name}', 期望 'deepseek-v4-flash'"
            )


def _reset_all_singletons():
    import sys
    modules = [f"app.agents.models.model_{n}" for n in
               ("scheduler","analyst","reviewer","risk","trader","super_analyst","solo")]
    for mod_name in modules:
        if mod_name in sys.modules:
            sys.modules[mod_name]._llm = None
