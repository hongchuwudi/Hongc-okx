"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_handoff.py 移交工具
描述: Agent 间移交控制权工具 — transfer_to_X

包含:
- transfer_to_analyst — 交给分析师
- transfer_to_reviewer — 交给复盘师
- transfer_to_risk — 交给风控师
- transfer_to_trader — 交给裁决员
- HANDOFF_SIGNAL — 移交信号标记
"""

from langchain_core.tools import tool

HANDOFF_SIGNAL = "__handoff_to__"


@tool
def transfer_to_analyst(reason: str = "") -> str:
    """将控制权移交给技术分析师。"""
    return f"{HANDOFF_SIGNAL}analyst|{reason}"


@tool
def transfer_to_reviewer(reason: str = "") -> str:
    """将控制权移交给复盘师。"""
    return f"{HANDOFF_SIGNAL}reviewer|{reason}"


@tool
def transfer_to_risk(reason: str = "") -> str:
    """将控制权移交给风控师。"""
    return f"{HANDOFF_SIGNAL}risk|{reason}"


@tool
def transfer_to_trader(reason: str = "") -> str:
    """将控制权移交给交易裁决员。"""
    return f"{HANDOFF_SIGNAL}trader|{reason}"
