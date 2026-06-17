"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: model_reviewer.py 复盘师模型
描述: 复盘师 LLM — deepseek-chat，历史模式识别，中等输出

包含:
- 函数: get_reviewer_llm — 返回复盘师 LLM 实例
"""

import httpx
from langchain_openai import ChatOpenAI

from app.core.config import config

_llm: ChatOpenAI | None = None

_client = httpx.Client(proxy=None)

# 复盘师模型：标准温度 + 500 token，输出经验教训。
def get_reviewer_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=config.ai.deepseek_api_key,
            base_url=config.ai.deepseek_base_url,
            temperature=0.3,
            max_tokens=500,
            http_client=_client,
        )
    return _llm
