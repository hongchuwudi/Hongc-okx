"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config_okx.py OKX配置
描述: OKX 交易所 API 配置，根据 OKX_SANDBOX 自动选择主账户/模拟账户

包含:
- 类: OKXConfig — OKX API 密钥 + 沙箱 + 代理
"""

import os
from dataclasses import dataclass


@dataclass
class OKXConfig:
    sandbox: bool = os.getenv("OKX_SANDBOX", "true").lower() == "true"
    proxy: str | None = os.getenv("HTTPS_PROXY")
    proxy_backup: str | None = os.getenv("HTTPS_PROXY_BACKUP")

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
