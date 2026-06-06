"""风控评估节点"""

from app.agents.shared import SupervisorState
from app.agents.parser import parse_agent_json_output
from app.agents.prompts.risk import RISK_SYSTEM
from app.agents.shared import get_llm
from app.logger import get_logger

logger = get_logger()


def risk_node(state: SupervisorState) -> dict:
    llm = get_llm()
    logger.info("[risk] 启动风控评估...")

    response = llm.invoke([
        {"role": "system", "content": RISK_SYSTEM},
        {"role": "user", "content": f"{state['market_text']}\n\n{state['position_text']}\n\n{state['memory_text']}\n\n请输出你的分析（严格 JSON）。"},
    ])
    raw = response.content if hasattr(response, "content") else str(response)
    parsed = parse_agent_json_output(raw)
    if parsed is not None:
        report = parsed.get("reasoning", parsed.get("reason", str(raw)[:300]))
        pos_pct = parsed.get("position_pct", 0)
        logger.info(f"[risk] → 仓位{pos_pct}%: {report[:80]}...")
    else:
        report = "风控分析暂时不可用"
        logger.warning("[risk] 解析失败")

    return {"risk_report": str(report), "messages": [response]}
