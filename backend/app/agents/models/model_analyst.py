"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: model_analyst.py 分析师模型
描述: 分析师 LLM — deepseek-chat，标准技术分析，需完整报告

包含:
- 函数: get_analyst_llm — 返回分析师 LLM 实例
"""

import httpx
from langchain_openai import ChatOpenAI

from app.core.config import config

_llm: ChatOpenAI | None = None

_client = httpx.Client(proxy=None)  # 直连 DeepSeek，不走代理

# 分析师模型：标准温度 + 800 token，输出含信号、趋势、证据。
def get_analyst_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=config.ai.deepseek_api_key,
            base_url=config.ai.deepseek_base_url,
            temperature=0.3,
            max_tokens=800,
            http_client=_client,
        )
    return _llm
