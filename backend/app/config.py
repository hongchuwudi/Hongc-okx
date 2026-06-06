"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: config.py 统一配置管理
描述: 统一配置管理 — 从 .env 文件读取所有配置项，提供类型安全的配置数据类

包含:
- 类: PostgresConfig — PostgreSQL 连接配置
- 类: RedisConfig — Redis 连接配置
- 类: OKXConfig — OKX 交易所 API 配置（沙箱/实盘）
- 类: AIConfig — AI 模型提供商配置（DeepSeek / DashScope）
- 类: TradeConfig — 交易参数配置
- 类: AppConfig — 顶层应用配置聚合
- 常量: config — 全局配置单例
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env
load_dotenv(Path(__file__).parent.parent / ".env")


# ── PostgreSQL 连接配置 ──────────────────────────────────────────
@dataclass
class PostgresConfig:
    """PostgreSQL 数据库连接参数及 URL 构造"""

    host: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    user: str = os.getenv("POSTGRES_USER", "root")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    database: str = os.getenv("POSTGRES_DB", "trading")
    pool_size: int = 5  # 连接池大小
    max_overflow: int = 10  # 连接池溢出上限

    @property
    def url(self) -> str:
        """返回同步连接 URL"""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def async_url(self) -> str:
        """返回异步连接 URL（asyncpg 驱动）"""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


# ── Redis 连接配置 ───────────────────────────────────────────────
@dataclass
class RedisConfig:
    """Redis 缓存与 Pub/Sub 连接参数"""

    host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    db: int = int(os.getenv("REDIS_DB", "12"))
    max_connections: int = 50  # 最大连接数

    @property
    def url(self) -> str:
        """返回 Redis 连接 URL"""
        return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"


# ── OKX 交易所配置 ───────────────────────────────────────────────
@dataclass
class OKXConfig:
    """OKX 交易所 API 凭证，根据 sandbox 标志选择沙箱或实盘密钥"""

    sandbox: bool = os.getenv("OKX_SANDBOX", "true").lower() == "true"

    @property
    def api_key(self) -> str:
        """返回对应模式的 API Key"""
        if self.sandbox:
            return os.getenv("OKX_DEMO_API_KEY", "")
        return os.getenv("OKX_MAIN_API_KEY", "")

    @property
    def secret(self) -> str:
        """返回对应模式的 Secret"""
        if self.sandbox:
            return os.getenv("OKX_DEMO_SECRET", "")
        return os.getenv("OKX_MAIN_SECRET", "")

    @property
    def password(self) -> str:
        """返回对应模式的 Password"""
        if self.sandbox:
            return os.getenv("OKX_DEMO_PASSWORD", "")
        return os.getenv("OKX_MAIN_PASSWORD", "")

    @property
    def proxy(self) -> str | None:
        """返回 HTTPS 代理地址（可选，用于国内服务器访问 OKX）"""
        return os.getenv("HTTPS_PROXY") or None


# ── AI 模型配置 ──────────────────────────────────────────────────
@dataclass
class AIConfig:
    """AI 模型提供商配置，支持 DeepSeek 和阿里 DashScope"""

    provider: str = os.getenv("AI_PROVIDER", "deepseek")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    cryptoracle_api_key: str = os.getenv("CRYPTORACLE_API_KEY", "")


# ── 交易参数配置 ─────────────────────────────────────────────────
@dataclass
class TradeConfig:
    """交易运行参数：品种、杠杆、时间周期、仓位管理、风控阈值"""

    symbol: str = "BTC/USDT:USDT"
    leverage: int = 1
    timeframe: str = "1h"
    data_points: int = 168  # 策略分析的历史 K 线数量
    base_usdt_amount: float = 1.0  # 单次开仓基准金额（USDT）
    max_position_ratio: float = 0.8  # 最大仓位占比
    max_daily_drawdown_pct: float = float(
        os.getenv("MAX_DAILY_DRAWDOWN_PCT", "10.0")
    )
    max_daily_loss_usdt: float = float(os.getenv("MAX_DAILY_LOSS_USDT", "50.0"))
    tick_interval_seconds: int = 180  # 交易引擎 tick 间隔（秒），3 分钟


# ── 顶层应用配置 ─────────────────────────────────────────────────
@dataclass
class AppConfig:
    """顶层配置聚合，包含所有子配置模块"""

    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    okx: OKXConfig = field(default_factory=OKXConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    trade: TradeConfig = field(default_factory=TradeConfig)


# 全局配置单例
config = AppConfig()
