"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_singleton.py config 全局单例测试
描述: 验证 config 是 AppConfig 实例且所有子模块存在
"""

from app.core.config import config, AppConfig


def test_config_is_appconfig_instance():
    assert isinstance(config, AppConfig)


def test_config_has_all_sub_modules():
    assert hasattr(config, "postgres"), "缺少 postgres 配置"
    assert hasattr(config, "redis"), "缺少 redis 配置"
    assert hasattr(config, "okx"), "缺少 okx 配置"
    assert hasattr(config, "ai"), "缺少 ai 配置"
    assert hasattr(config, "trade"), "缺少 trade 配置"


def test_config_env_has_default():
    assert config.env in ("development", "production", "test")
