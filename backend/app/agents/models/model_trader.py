"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: model_trader.py 交易裁决员模型
描述: 交易裁决员 LLM — deepseek-reasoner，深度推理综合决策

包含:
- 函数: get_trader_llm — 返回交易裁决员 LLM 实例
"""

from langchain_openai import ChatOpenAI
from app.config import config

_llm: ChatOpenAI | None = None


def get_trader_llm() -> ChatOpenAI:
    """交易裁决员模型：deepseek-reasoner 深度推理，1200 token 完整决策链。"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="deepseek-reasoner",
            api_key=config.ai.deepseek_api_key,
            base_url=config.ai.deepseek_base_url,
            temperature=0.2,
            max_tokens=1200,
        )
    return _llm
