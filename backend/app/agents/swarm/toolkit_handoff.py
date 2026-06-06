"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_handoff.py 移交工具
描述: Agent 间移交控制权的工具 — 模仿 Swarm 的 transfer_to_X 模式

包含:
- transfer_to_analyst — 交给分析师
- transfer_to_reviewer — 交给复盘师
- transfer_to_risk — 交给风控师
- transfer_to_trader — 交给交易裁决员
- HANDOFF_SIGNAL — 移交信号标记
"""

from langchain_core.tools import tool

HANDOFF_SIGNAL = "__handoff_to__"


@tool
def transfer_to_analyst(reason: str = "") -> str:
    """将控制权移交给技术分析师。当需要重新分析行情或修正分析结论时调用。"""
    return f"{HANDOFF_SIGNAL}analyst|{reason}"


@tool
def transfer_to_reviewer(reason: str = "") -> str:
    """将控制权移交给复盘师。当需要查阅历史数据或经验教训时调用。"""
    return f"{HANDOFF_SIGNAL}reviewer|{reason}"


@tool
def transfer_to_risk(reason: str = "") -> str:
    """将控制权移交给风控师。当需要风险评估或仓位边界时调用。"""
    return f"{HANDOFF_SIGNAL}risk|{reason}"


@tool
def transfer_to_trader(reason: str = "") -> str:
    """将控制权移交给交易裁决员。当分析完成可以进入最终决策时调用。"""
    return f"{HANDOFF_SIGNAL}trader|{reason}"


tools = [transfer_to_analyst, transfer_to_reviewer, transfer_to_risk, transfer_to_trader]
