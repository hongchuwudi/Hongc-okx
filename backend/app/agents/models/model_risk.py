"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: model_risk.py 风控师模型
描述: 风控师 LLM — deepseek-chat，低温度保证风控输出稳定可重复

包含:
- 函数: get_risk_llm — 返回风控师 LLM 实例
"""

from langchain_openai import ChatOpenAI
from app.config import config

_llm: ChatOpenAI | None = None


def get_risk_llm() -> ChatOpenAI:
    """风控师模型：温度 0.1 保证确定性输出，风控决策不能随机。"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=config.ai.deepseek_api_key,
            base_url=config.ai.deepseek_base_url,
            temperature=0.1,
            max_tokens=600,
        )
    return _llm
