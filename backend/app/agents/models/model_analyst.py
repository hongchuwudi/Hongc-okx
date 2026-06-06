"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: model_analyst.py 分析师模型
描述: 分析师 LLM — deepseek-chat，标准技术分析，需完整报告

包含:
- 函数: get_analyst_llm — 返回分析师 LLM 实例
"""

from langchain_openai import ChatOpenAI
from app.config import config

_llm: ChatOpenAI | None = None


def get_analyst_llm() -> ChatOpenAI:
    """分析师模型：标准温度 + 800 token，输出含信号、趋势、证据。"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=config.ai.deepseek_api_key,
            base_url=config.ai.deepseek_base_url,
            temperature=0.3,
            max_tokens=800,
        )
    return _llm
