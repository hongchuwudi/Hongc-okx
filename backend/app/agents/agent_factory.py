"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: agent_factory.py Agent工厂
描述: 5 个 Agent 的构建逻辑，集中管理模型/工具/提示词的装配

包含:
- 函数: build_agents — 返回 5 个 Agent 字典 {name: compiled_graph}
"""

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from app.agents.models import (
    get_scheduler_llm, get_analyst_llm, get_reviewer_llm, get_risk_llm, get_trader_llm,
)
from app.agents.prompts import SCHEDULER_PROMPT, ANALYST_PROMPT, REVIEWER_PROMPT, RISK_PROMPT, TRADER_PROMPT
from app.agents.toolkits.tools.toolkit_memory_private import create_memory_tools
from app.logger import get_logger

logger = get_logger()


def build_agents() -> dict:
    """构建 5 个 Agent，返回 {name: compiled_subgraph}。"""
    from app.agents.toolkits.toolkit_market import tools as mkt_tools
    from app.agents.toolkits.toolkit_position import tools as pos_tools
    from app.agents.toolkits.toolkit_risk import tools as risk_tools
    from app.agents.toolkits.toolkit_memory import tools as mem_tools
    from app.agents.toolkits.communication.toolkit_handoff import (
        transfer_to_analyst, transfer_to_reviewer, transfer_to_risk, transfer_to_trader,
    )
    from app.agents.toolkits.communication.toolkit_dialogue import (
        ask_analyst, ask_reviewer, ask_risk,
    )

    logger.info(f"工具: market={len(mkt_tools)} position={len(pos_tools)} risk={len(risk_tools)} memory={len(mem_tools)}")

    sch_mem = create_memory_tools("scheduler"); ana_mem = create_memory_tools("analyst")
    rev_mem = create_memory_tools("reviewer"); risk_mem = create_memory_tools("risk")
    trader_mem = create_memory_tools("trader")
    H = ("\n你拥有 check_my_accuracy 工具查看自己的历史准确率。"
         "\n每次做预测时先 remember('prediction','你的预测内容')，看到反馈后 remember('result_xxx','对了/错了+原因')。")

    return {
        "scheduler": create_react_agent(
            model=get_scheduler_llm().bind_tools([transfer_to_analyst, transfer_to_reviewer] + sch_mem),
            tools=[transfer_to_analyst, transfer_to_reviewer] + sch_mem,
            prompt=SystemMessage(content=SCHEDULER_PROMPT + H), name="scheduler",
        ),
        "analyst": create_react_agent(
            model=get_analyst_llm().bind_tools(mkt_tools + [transfer_to_risk, ask_reviewer, ask_risk] + ana_mem),
            tools=mkt_tools + [transfer_to_risk, ask_reviewer, ask_risk] + ana_mem,
            prompt=SystemMessage(content=ANALYST_PROMPT + H), name="analyst",
        ),
        "reviewer": create_react_agent(
            model=get_reviewer_llm().bind_tools(mem_tools + [transfer_to_risk, ask_analyst, ask_risk] + rev_mem),
            tools=mem_tools + [transfer_to_risk, ask_analyst, ask_risk] + rev_mem,
            prompt=SystemMessage(content=REVIEWER_PROMPT + H), name="reviewer",
        ),
        "risk": create_react_agent(
            model=get_risk_llm().bind_tools(risk_tools + [transfer_to_analyst, transfer_to_trader, ask_analyst, ask_reviewer] + risk_mem),
            tools=risk_tools + [transfer_to_analyst, transfer_to_trader, ask_analyst, ask_reviewer] + risk_mem,
            prompt=SystemMessage(content=RISK_PROMPT + H), name="risk",
        ),
        "trader": create_react_agent(
            model=get_trader_llm().bind_tools([ask_risk] + trader_mem),
            tools=[ask_risk] + trader_mem,
            prompt=SystemMessage(content=TRADER_PROMPT + H), name="trader",
        ),
    }
