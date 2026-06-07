"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: __init__.py 配置模块导出
描述: 组合所有子配置，暴露 config 全局单例

包含:
- 类: AppConfig — 顶层配置，组合所有子模块
- 变量: config — AppConfig 全局单例
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


@dataclass
class AppConfig:
    """顶层配置，组合各子模块。"""
    env: str = os.getenv("ENV", "development")
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    okx: OKXConfig = field(default_factory=OKXConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    trade: TradeConfig = field(default_factory=TradeConfig)


config = AppConfig()
