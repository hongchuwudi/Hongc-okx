"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: config_ai.py AI配置
描述: AI 模型 API 配置（DeepSeek / Qwen）

包含:
- 类: AIConfig — AI API 密钥和 Base URL
"""

import os
from dataclasses import dataclass


@dataclass
class AIConfig:
    provider: str = os.getenv("AI_PROVIDER", "deepseek")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    qwen_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    qwen_base_url: str = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    cryptoracle_api_key: str = os.getenv("CRYPTORACLE_API_KEY", "")
