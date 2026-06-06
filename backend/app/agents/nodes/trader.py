"""交易决策节点"""

from app.agents.shared import SupervisorState
from app.agents.parser import parse_agent_json_output
from app.agents.prompts.trader import TRADER_SYSTEM
from app.agents.shared import get_llm
from app.logger import get_logger

logger = get_logger()


def trader_node(state: SupervisorState) -> dict:
    llm = get_llm()
    logger.info("[trader] 综合决策中...")

    reports = []
    if state.get("market_report"):
        reports.append(f"【市场分析】\n{state['market_report']}")
    if state.get("risk_report"):
        reports.append(f"【风控评估】\n{state['risk_report']}")
    if state.get("memory_report"):
        reports.append(f"【复盘建议】\n{state['memory_report']}")
    combined = "\n\n".join(reports) if reports else "无 Agent 报告，请基于行情数据独立判断。"

    prompt = (
        f"【行情数据】\n{state['market_text']}\n\n"
        f"【持仓】\n{state['position_text']}\n\n"
        f"【Agent 报告】\n{combined}\n\n"
        f"请综合以上所有信息，输出最终交易决策（严格 JSON）。"
    )

    response = llm.invoke([
        {"role": "system", "content": TRADER_SYSTEM},
        {"role": "user", "content": prompt},
    ])
    raw = response.content if hasattr(response, "content") else str(response)

    parsed = parse_agent_json_output(raw)
    if parsed is not None:
        s = parsed.get("signal", "HOLD")
        if isinstance(s, str):
            s = s.upper()
        decision = {
            "signal": s if s in ("BUY", "SELL", "HOLD") else "HOLD",
            "confidence": parsed.get("confidence", "MEDIUM"),
            "reason": str(parsed.get("reason", parsed.get("reasoning", "")))[:200],
            "stop_loss": float(parsed.get("stop_loss", parsed.get("sl", state["price"] * 0.98)) or state["price"] * 0.98),
            "take_profit": float(parsed.get("take_profit", parsed.get("tp", state["price"] * 1.02)) or state["price"] * 1.02),
            "position_pct": float(parsed.get("position_pct", 0) or 0),
        }
    else:
        decision = {
            "signal": "HOLD", "confidence": "LOW",
            "reason": "Trader 决策解析失败，保守观望",
            "stop_loss": state["price"] * 0.98,
            "take_profit": state["price"] * 1.02,
            "position_pct": 0,
        }
        logger.warning("[trader] 解析失败，使用 HOLD 回退")

    logger.info(f"[trader] 最终决策: {decision['signal']} ({decision['confidence']})")
    return {"final_decision": decision}
