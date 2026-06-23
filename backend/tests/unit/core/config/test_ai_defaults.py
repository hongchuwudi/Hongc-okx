"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_ai_defaults.py AIConfig 默认值测试
描述: 验证 AIConfig 默认 provider 和 base_url
"""

from app.core.config import config


def test_ai_config_has_valid_provider():
    assert config.ai.provider in ("deepseek", "qwen"), (
        f"provider={config.ai.provider} 必须为 deepseek 或 qwen"
    )


def test_ai_config_has_base_url():
    assert config.ai.deepseek_base_url.startswith("https://"), (
        f"base_url={config.ai.deepseek_base_url} 必须以 https:// 开头"
    )
