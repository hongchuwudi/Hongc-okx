"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_api_key.py API Key 配置测试
描述: 验证所有模型的 api_key 已从环境变量加载
"""

import pytest
from unittest.mock import patch

from app.core.config import config as cfg


@pytest.mark.skipif(
    not cfg.ai.deepseek_api_key or "your-" in cfg.ai.deepseek_api_key,
    reason="DEEPSEEK_API_KEY 未配置，跳过 API Key 测试"
)
def test_all_models_have_api_key_configured():
    """所有模型实例的 api_key 必须非空。"""
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
        key = getattr(llm, "openai_api_key", None) or getattr(llm, "api_key", None)
        assert key, f"{name} 模型的 api_key 为空"
        assert "your-" not in str(key), f"{name} 模型的 api_key 为占位符"
