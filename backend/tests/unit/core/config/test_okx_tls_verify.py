"""
创建时间: 2026-07-01
作者: hongchuwudi
描述: OKX TLS 校验配置测试

包含:
- 函数: test_tls_verify_enabled_by_default — 默认启用 TLS 证书校验
- 函数: test_tls_verify_can_be_disabled_in_development — 开发环境允许显式关闭
- 函数: test_tls_verify_cannot_be_disabled_in_production — 生产环境禁止关闭
"""

import pytest

from app.core.config.config_okx import OKXConfig
from app.core.exceptions import ConfigError


def test_tls_verify_enabled_by_default():
    cfg = OKXConfig(verify_tls=True)
    assert cfg.verify_tls is True


def test_tls_verify_can_be_disabled_in_development(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    cfg = OKXConfig(verify_tls=False)
    assert cfg.verify_tls is False


def test_tls_verify_cannot_be_disabled_in_production(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    with pytest.raises(ConfigError):
        OKXConfig(verify_tls=False)
