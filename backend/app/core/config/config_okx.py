"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config_okx.py OKX配置
描述: OKX 交易所 API 配置，根据 OKX_SANDBOX 自动选择主账户/模拟账户

包含:
- 类: OKXConfig — OKX API 密钥 + 沙箱 + 代理 + TLS 校验
"""

import os
from dataclasses import dataclass

from app.core.exceptions import ConfigError


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class OKXConfig:
    sandbox: bool = os.getenv("OKX_SANDBOX", "true").lower() == "true"
    proxy: str | None = os.getenv("HTTPS_PROXY")
    proxy_backup: str | None = os.getenv("HTTPS_PROXY_BACKUP")
    verify_tls: bool = _env_bool("OKX_VERIFY_TLS", True)

    def __post_init__(self) -> None:
        env = os.getenv("ENV", "development").strip().lower()
        if not self.verify_tls and env not in ("development", "local", "test", "testing"):
            raise ConfigError("OKX_VERIFY_TLS=false 仅允许在 development/local/test 环境使用")

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
