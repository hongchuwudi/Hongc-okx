"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config_okx.py OKX配置
描述: OKX 交易所 API 配置

包含:
- 类: OKXConfig — OKX API 密钥 + 模拟盘 + 代理
"""

import os
from dataclasses import dataclass


@dataclass
class OKXConfig:
    api_key: str = os.getenv("OKX_API_KEY", "")
    secret: str = os.getenv("OKX_SECRET", "")
    password: str = os.getenv("OKX_PASSWORD", "")
    sandbox: bool = os.getenv("OKX_SANDBOX", "true").lower() == "true"
    proxy: str | None = os.getenv("HTTPS_PROXY")
