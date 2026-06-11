"""
创建时间: 2026-06-14
作者: hongchuwudi
文件名: model_solo.py 单Agent模型
描述: Solo Agent LLM — deepseek-v4-flash，低温保证风控稳定

包含:
- 函数: get_solo_llm — 返回 Solo Agent LLM 实例
"""

import httpx
from langchain_openai import ChatOpenAI

from app.config import config

_llm: ChatOpenAI | None = None

_client = httpx.Client(proxy=None)  # 直连 DeepSeek，不走代理

# Solo Agent 模型：低温 0.15 + 1500 token，兼顾风控稳定性与分析深度。
def get_solo_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=config.ai.deepseek_api_key,
            base_url=config.ai.deepseek_base_url,
            temperature=0.15,
            max_tokens=1500,
            http_client=_client,
        )
    return _llm
