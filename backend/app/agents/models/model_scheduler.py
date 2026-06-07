"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: model_scheduler.py 调度师模型
描述: 调度师 LLM — deepseek-chat，轻量快扫，低 token 上限

包含:
- 函数: get_scheduler_llm — 返回调度师 LLM 实例
"""

from langchain_openai import ChatOpenAI
from app.config import config

_llm: ChatOpenAI | None = None


def get_scheduler_llm() -> ChatOpenAI:
    """调度师模型：轻量快速扫描市场状态，300 token 足够输出 JSON。"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=config.ai.deepseek_api_key,
            base_url=config.ai.deepseek_base_url,
            temperature=0.3,
            max_tokens=300,
        )
    return _llm
