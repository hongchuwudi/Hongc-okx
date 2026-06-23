"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_system_prompt.py SystemMessage 测试
描述: 验证 factory 构建的 Agent 包含 SystemMessage 且内容非空
"""

import sys
from unittest.mock import patch, MagicMock

from langchain_core.messages import SystemMessage


def test_build_agents_sets_system_prompt():
    """build_agents() 传递的 prompt 是 SystemMessage 且内容非空。"""
    captured_prompts = []

    def capture_create(**kwargs):
        prompt = kwargs.get("prompt")
        captured_prompts.append((kwargs.get("name"), prompt))
        ag = MagicMock()
        ag.name = kwargs.get("name", "unknown")
        return ag

    with patch.dict(sys.modules, _mock_pandas_ta()), \
         patch('app.core.config.config.ai.deepseek_api_key', 'test-key'), \
         patch('app.agents.agent_factory.create_react_agent', side_effect=capture_create), \
         patch('app.agents.agent_factory.get_prompt_sync', return_value="test prompt content"):
        from app.agents.agent_factory import build_agents
        build_agents()

    assert len(captured_prompts) == 5, f"期望 5 个 Agent, 捕获 {len(captured_prompts)}"
    for name, prompt in captured_prompts:
        assert isinstance(prompt, SystemMessage), (
            f"{name} 的 prompt 不是 SystemMessage: {type(prompt)}"
        )
        assert prompt.content.strip(), f"{name} 的 SystemMessage 内容为空"


def test_build_agents_3_sets_system_prompt():
    """build_agents_3() 传递的 prompt 是 SystemMessage 且内容非空。"""
    captured_prompts = []

    def capture_create(**kwargs):
        captured_prompts.append((kwargs.get("name"), kwargs.get("prompt")))
        ag = MagicMock()
        ag.name = kwargs.get("name", "unknown")
        return ag

    with patch.dict(sys.modules, _mock_pandas_ta()), \
         patch('app.core.config.config.ai.deepseek_api_key', 'test-key'), \
         patch('app.agents.agent_factory.create_react_agent', side_effect=capture_create), \
         patch('app.agents.agent_factory.get_prompt_sync', return_value="test super prompt"):
        from app.agents.agent_factory import build_agents_3
        build_agents_3()

    assert len(captured_prompts) == 3
    for name, prompt in captured_prompts:
        assert isinstance(prompt, SystemMessage), f"{name} prompt 不是 SystemMessage"
        assert prompt.content.strip(), f"{name} 的 SystemMessage 内容为空"


def test_build_agent_solo_sets_system_prompt():
    """build_agent_solo() 传递的 prompt 是 SystemMessage 且内容非空。"""
    captured_prompt = {}

    def capture_create(**kwargs):
        captured_prompt["name"] = kwargs.get("name")
        captured_prompt["prompt"] = kwargs.get("prompt")
        ag = MagicMock()
        ag.name = kwargs.get("name", "unknown")
        return ag

    with patch('app.core.config.config.ai.deepseek_api_key', 'test-key'), \
         patch('app.agents.agent_factory.create_react_agent', side_effect=capture_create), \
         patch('app.agents.agent_factory.get_prompt_sync', return_value="test solo prompt"):
        from app.agents.agent_factory import build_agent_solo
        build_agent_solo()

    assert captured_prompt["name"] == "solo"
    prompt = captured_prompt["prompt"]
    assert isinstance(prompt, SystemMessage), f"prompt 不是 SystemMessage"
    assert prompt.content.strip(), "SystemMessage 内容为空"


def _mock_pandas_ta():
    fake_ta = MagicMock()
    fake_ta.rsi = MagicMock(return_value=MagicMock())
    fake_ta.macd = MagicMock(return_value=MagicMock())
    fake_ta.sma = MagicMock(return_value=MagicMock())
    fake_ta.bbands = MagicMock(return_value=MagicMock())
    fake_ta.atr = MagicMock(return_value=MagicMock())
    return {"pandas_ta": fake_ta}
