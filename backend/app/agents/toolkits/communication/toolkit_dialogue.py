"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_dialogue.py 对话工具
描述: Agent 间互问工具 — ask_X

包含:
- ask_analyst — 向分析师提问
- ask_reviewer — 向复盘师提问
- ask_risk — 向风控师提问
- ASK_SIGNAL — 对话信号标记
"""

from langchain_core.tools import tool

ASK_SIGNAL = "__ask__"


@tool
def ask_analyst(question: str) -> str:
    """向技术分析师提问。"""
    return f"{ASK_SIGNAL}analyst|{question}"


@tool
def ask_reviewer(question: str) -> str:
    """向复盘师提问。"""
    return f"{ASK_SIGNAL}reviewer|{question}"


@tool
def ask_risk(question: str) -> str:
    """向风控师提问。"""
    return f"{ASK_SIGNAL}risk|{question}"
