"""统一配置管理 — 从 .env 读取所有配置"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env
load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class PostgresConfig:
    host: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    user: str = os.getenv("POSTGRES_USER", "root")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    database: str = os.getenv("POSTGRES_DB", "trading")
    pool_size: int = 5
    max_overflow: int = 10

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    db: int = int(os.getenv("REDIS_DB", "12"))
    max_connections: int = 50

    @property
    def url(self) -> str:
        return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"


@dataclass
class OKXConfig:
    sandbox: bool = os.getenv("OKX_SANDBOX", "true").lower() == "true"

    @property
    def api_key(self) -> str:
        if self.sandbox:
            return os.getenv("OKX_DEMO_API_KEY", "")
        return os.getenv("OKX_MAIN_API_KEY", "")

    @property
    def secret(self) -> str:
        if self.sandbox:
            return os.getenv("OKX_DEMO_SECRET", "")
        return os.getenv("OKX_MAIN_SECRET", "")

    @property
    def password(self) -> str:
        if self.sandbox:
            return os.getenv("OKX_DEMO_PASSWORD", "")
        return os.getenv("OKX_MAIN_PASSWORD", "")

    @property
    def proxy(self) -> str | None:
        return os.getenv("HTTPS_PROXY") or None


@dataclass
class AIConfig:
    provider: str = os.getenv("AI_PROVIDER", "deepseek")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    cryptoracle_api_key: str = os.getenv("CRYPTORACLE_API_KEY", "")


@dataclass
class TradeConfig:
    symbol: str = "BTC/USDT:USDT"
    leverage: int = 1
    timeframe: str = "1h"
    data_points: int = 168
    base_usdt_amount: float = 1.0
    max_position_ratio: float = 0.8
    max_daily_drawdown_pct: float = float(
        os.getenv("MAX_DAILY_DRAWDOWN_PCT", "10.0")
    )
    max_daily_loss_usdt: float = float(os.getenv("MAX_DAILY_LOSS_USDT", "50.0"))
    tick_interval_seconds: int = 60


@dataclass
class AppConfig:
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    okx: OKXConfig = field(default_factory=OKXConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    trade: TradeConfig = field(default_factory=TradeConfig)


# 全局单例
config = AppConfig()
