"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: __init__.py 配置模块导出
描述: 组合所有子配置，暴露 config 全局单例 + get_config 工厂函数

包含:
- 类: AppConfig — 顶层配置，组合所有子模块
- 变量: config — AppConfig 全局单例（生产环境直接 import 使用）
- 函数: get_config — 创建可覆盖的配置实例（测试环境注入不同配置）
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 加载 backend/.env
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from app.config.config_postgres import PostgresConfig
from app.config.config_redis import RedisConfig
from app.config.config_okx import OKXConfig
from app.config.config_ai import AIConfig
from app.config.config_trade import TradeConfig


# 顶层配置，组合各子模块。
@dataclass
class AppConfig:
    env: str = os.getenv("ENV", "development")
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    okx: OKXConfig = field(default_factory=OKXConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    trade: TradeConfig = field(default_factory=TradeConfig)


# 全局单例 — 生产代码直接 from app.config import config 使用
config = AppConfig()


# 创建可覆盖的配置实例 — 测试环境注入不同配置：
#   from app.config import get_config
#   cfg = get_config(trade=TradeConfig(symbol="ETH/USDT:USDT"))
def get_config(**overrides) -> AppConfig:
    kwargs = {k: v for k, v in vars(config).items() if not k.startswith("_")}
    kwargs.update(overrides)
    return AppConfig(**kwargs)

