"""共享模块 — LLM 客户端 + State 定义（避免 graph ↔ nodes 循环导入）"""

from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from app.config import config

# ── State ─────────────────────────────────────────────────

class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    market_text: str
    position_text: str
    memory_text: str
    atr_pct: float
    market_report: str
    risk_report: str
    memory_report: str
    next_agent: str
    final_decision: dict
    price: float
    equity: float

# ── LLM ───────────────────────────────────────────────────

_llm: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    """全局单例 LLM 客户端。"""
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
