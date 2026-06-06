"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_dialogue.py 对话工具
描述: Agent 间互问工具 — 分析师可以问复盘师、复盘师可以问分析师，打破单向流水线

包含:
- ask_analyst — 向技术分析师提问
- ask_reviewer — 向复盘师提问
- ask_risk — 向风控师提问
- ask_trader — 向交易裁决员提问
- ASK_SIGNAL — 对话信号标记
"""

from langchain_core.tools import tool

ASK_SIGNAL = "__ask__"


@tool
def ask_analyst(question: str) -> str:
    """向技术分析师提问。当你需要了解技术指标细节、RSI含义、趋势判断依据时调用。"""
    return f"{ASK_SIGNAL}analyst|{question}"


@tool
def ask_reviewer(question: str) -> str:
    """向复盘师提问。当你需要了解历史类似形态的胜率、近期交易统计时调用。"""
    return f"{ASK_SIGNAL}reviewer|{question}"


@tool
def ask_risk(question: str) -> str:
    """向风控师提问。当你需要了解仓位边界、风险评估依据时调用。"""
    return f"{ASK_SIGNAL}risk|{question}"


@tool
def ask_trader(question: str) -> str:
    """向交易裁决员提问。当你需要确认最终决策逻辑时调用。"""
    return f"{ASK_SIGNAL}trader|{question}"


tools = [ask_analyst, ask_reviewer, ask_risk, ask_trader]
