"""StateGraph 路由 + 构建

图结构:
  START → supervisor → {market, risk, memory, trader}
  market/risk/memory → supervisor (循环直到 FINISH/超限)
  trader → END
"""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    supervisor_node,
    market_node,
    risk_node,
    memory_node,
    trader_node,
)
from app.agents.shared import SupervisorState
from app.logger import get_logger

logger = get_logger()

# ── 路由 ───────────────────────────────────────────────────

def _router(state: SupervisorState) -> Literal["market", "risk", "memory", "trader"]:
    agent = state.get("next_agent", "trader")
    if agent not in ("market", "risk", "memory", "trader"):
        agent = "trader"
    return agent  # type: ignore

# ── 图构建 ─────────────────────────────────────────────────

def build_supervisor_graph() -> StateGraph:
    builder = StateGraph(SupervisorState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("market", market_node)
    builder.add_node("risk", risk_node)
    builder.add_node("memory", memory_node)
    builder.add_node("trader", trader_node)

    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges("supervisor", _router, {
        "market": "market",
        "risk": "risk",
        "memory": "memory",
        "trader": "trader",
    })

    builder.add_edge("market", "supervisor")
    builder.add_edge("risk", "supervisor")
    builder.add_edge("memory", "supervisor")

    builder.add_edge("trader", END)

    graph = builder.compile()
    logger.info("Supervisor Graph 编译完成")
    return graph
