"""Supervisor 调度节点"""

from app.agents.shared import SupervisorState
from app.agents.parser import parse_agent_json_output
from app.agents.prompts.supervisor import SUPERVISOR_SYSTEM
from app.agents.shared import get_llm
from app.logger import get_logger

logger = get_logger()


def supervisor_node(state: SupervisorState) -> dict:
    llm = get_llm()
    msgs = state["messages"]

    status_parts = []
    if state.get("market_report"):
        status_parts.append("market: 已完成")
    if state.get("risk_report"):
        status_parts.append("risk: 已完成")
    if state.get("memory_report"):
        status_parts.append("memory: 已完成")
    status = "\n".join(status_parts) if status_parts else "暂无报告"

    market_context = (
        f"价格: ${state['price']:,.2f} | 权益: ${state['equity']:,.0f} | ATR: {state['atr_pct']:.1f}%"
    )

    system = SUPERVISOR_SYSTEM.format(market_context=market_context)
    prompt = (
        f"已有报告:\n{status}\n\n"
        f"请决定下一步（market/risk/memory/trader/FINISH），输出 JSON。"
    )

    response = llm.invoke([
        {"role": "system", "content": system},
        *msgs,
        {"role": "user", "content": prompt},
    ])
    raw = response.content if hasattr(response, "content") else str(response)

    parsed = parse_agent_json_output(raw)
    next_agent = "trader"
    reason = ""
    if parsed:
        next_agent = parsed.get("next_agent", "trader")
        reason = parsed.get("reason", "")

    report_count = sum(1 for r in [
        state.get("market_report"), state.get("risk_report"), state.get("memory_report")
    ] if r)
    if report_count >= 2 and next_agent not in ("trader", "FINISH"):
        logger.info(f"Supervisor: 已 {report_count} 报告, 仍调 {next_agent} ({reason})")

    if next_agent == "FINISH":
        next_agent = "trader"

    logger.info(f"Supervisor → {next_agent} ({reason})")
    return {"next_agent": next_agent}
