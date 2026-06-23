"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_config_error.py ConfigError 测试
描述: 验证 ConfigError status_code=500
"""

from app.core.exceptions import ConfigError


def test_config_error_has_status_500():
    ex = ConfigError("DEEPSEEK_API_KEY not set")
    assert ex.status_code == 500
    assert "DEEPSEEK" in ex.message
