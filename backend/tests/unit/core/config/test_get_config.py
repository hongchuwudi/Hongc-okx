"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_get_config.py get_config 工厂函数测试
描述: 验证 get_config 创建可覆盖的配置实例
"""

from app.core.config import get_config
from app.core.config.config_trade import TradeConfig


def test_get_config_returns_new_instance():
    a = get_config()
    b = get_config()
    assert a is not b, "每次调用应返回新实例"


def test_get_config_supports_override():
    cfg = get_config(trade=TradeConfig(symbol="ETH/USDT:USDT"))
    assert cfg.trade.symbol == "ETH/USDT:USDT"


def test_get_config_preserves_other_modules():
    cfg = get_config(trade=TradeConfig(symbol="BTC/USDT:USDT"))
    assert cfg.ai is not None, "覆盖 trade 不应影响 ai 配置"
    assert cfg.postgres is not None, "覆盖 trade 不应影响 postgres 配置"
