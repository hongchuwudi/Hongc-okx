"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: model_trader.py 交易裁决员模型
描述: 交易裁决员 LLM — deepseek-reasoner，深度推理综合决策

包含:
- 函数: get_trader_llm — 返回交易裁决员 LLM 实例
"""

import httpx
from langchain_openai import ChatOpenAI

from app.core.config import config

_llm: ChatOpenAI | None = None

_client = httpx.Client(proxy=None)

# 交易裁决员模型：deepseek-reasoner 深度推理，1200 token 完整决策链。
def get_trader_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=config.ai.deepseek_api_key,
            base_url=config.ai.deepseek_base_url,
            temperature=0.2,
            max_tokens=2000,
            http_client=_client,
        )
    return _llm
