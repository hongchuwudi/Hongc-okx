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
    get_super_analyst_llm, get_solo_llm,
)
from app.agents.prompts import get_prompt_sync
from app.agents.toolkits.tools.toolkit_memory_private import create_memory_tools
from app.core.logger import get_logger

logger = get_logger()


# 构建 5 个 Agent，返回 {name: compiled_subgraph}。
def build_agents() -> dict:
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

    return {
        "scheduler": create_react_agent(
            model=get_scheduler_llm().bind_tools([transfer_to_analyst, transfer_to_reviewer] + sch_mem),
            tools=[transfer_to_analyst, transfer_to_reviewer] + sch_mem,
            prompt=SystemMessage(content=get_prompt_sync("scheduler")), name="scheduler",
        ),
        "analyst": create_react_agent(
            model=get_analyst_llm().bind_tools(mkt_tools + [transfer_to_risk, ask_reviewer, ask_risk] + ana_mem),
            tools=mkt_tools + [transfer_to_risk, ask_reviewer, ask_risk] + ana_mem,
            prompt=SystemMessage(content=get_prompt_sync("analyst")), name="analyst",
        ),
        "reviewer": create_react_agent(
            model=get_reviewer_llm().bind_tools(mem_tools + [transfer_to_risk, ask_analyst, ask_risk] + rev_mem),
            tools=mem_tools + [transfer_to_risk, ask_analyst, ask_risk] + rev_mem,
            prompt=SystemMessage(content=get_prompt_sync("reviewer")), name="reviewer",
        ),
        "risk": create_react_agent(
            model=get_risk_llm().bind_tools(risk_tools + [transfer_to_analyst, transfer_to_trader, ask_analyst, ask_reviewer] + risk_mem),
            tools=risk_tools + [transfer_to_analyst, transfer_to_trader, ask_analyst, ask_reviewer] + risk_mem,
            prompt=SystemMessage(content=get_prompt_sync("risk")), name="risk",
        ),
        "trader": create_react_agent(
            model=get_trader_llm().bind_tools([ask_risk] + trader_mem),
            tools=[ask_risk] + trader_mem,
            prompt=SystemMessage(content=get_prompt_sync("trader")), name="trader",
        ),
    }


# 构建 3 Agent 快速模式: 超级分析师 → 风控师 → 交易裁决员。
def build_agents_3() -> dict:
    from app.agents.toolkits.toolkit_market import tools as mkt_tools
    from app.agents.toolkits.toolkit_risk import tools as risk_tools
    from app.agents.toolkits.toolkit_memory import tools as mem_tools
    from app.agents.toolkits.communication.toolkit_handoff import (
        transfer_to_risk, transfer_to_super_analyst, transfer_to_trader,
    )
    from app.agents.toolkits.communication.toolkit_dialogue import (
        ask_risk,
    )

    logger.info(f"工具(3 Agent): market={len(mkt_tools)} risk={len(risk_tools)} memory={len(mem_tools)}")

    sa_mem = create_memory_tools("super_analyst")
    risk_mem = create_memory_tools("risk")
    trader_mem = create_memory_tools("trader")

    return {
        "super_analyst": create_react_agent(
            model=get_super_analyst_llm().bind_tools(
                mkt_tools + mem_tools + [transfer_to_risk, ask_risk] + sa_mem
            ),
            tools=mkt_tools + mem_tools + [transfer_to_risk, ask_risk] + sa_mem,
            prompt=SystemMessage(content=get_prompt_sync("super_analyst")), name="super_analyst",
        ),
        "risk": create_react_agent(
            model=get_risk_llm().bind_tools(
                risk_tools + [transfer_to_super_analyst, transfer_to_trader] + risk_mem
            ),
            tools=risk_tools + [transfer_to_super_analyst, transfer_to_trader] + risk_mem,
            prompt=SystemMessage(content=get_prompt_sync("risk")), name="risk",
        ),
        "trader": create_react_agent(
            model=get_trader_llm().bind_tools([ask_risk] + trader_mem),
            tools=[ask_risk] + trader_mem,
            prompt=SystemMessage(content=get_prompt_sync("trader")), name="trader",
        ),
    }


# 构建 1 Agent 急速模式: 全能交易员。
# 技术指标和风控参数由 coordinator 预计算注入，Agent 只需历史回顾 + 决策。
def build_agent_solo():
    from app.agents.toolkits.toolkit_memory import tools as mem_tools

    solo_mem = create_memory_tools("solo")
    all_tools = mem_tools + solo_mem

    logger.info(f"工具(Solo): memory={len(mem_tools)} private={len(solo_mem)} (指标/风控已预计算注入)")

    return create_react_agent(
        model=get_solo_llm().bind_tools(all_tools),
        tools=all_tools,
        prompt=SystemMessage(content=get_prompt_sync("solo")), name="solo",
    )
