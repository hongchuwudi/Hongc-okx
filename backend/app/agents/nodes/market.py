"""市场技术分析节点"""

from app.agents.shared import SupervisorState
from app.agents.parser import parse_agent_json_output
from app.agents.prompts.market import MARKET_SYSTEM
from app.agents.shared import get_llm
from app.logger import get_logger

logger = get_logger()


def market_node(state: SupervisorState) -> dict:
    llm = get_llm()
    logger.info("[market] 启动技术分析...")

    response = llm.invoke([
        {"role": "system", "content": MARKET_SYSTEM},
        {"role": "user", "content": f"{state['market_text']}\n\n{state['position_text']}\n\n请输出你的分析（严格 JSON）。"},
    ])
    raw = response.content if hasattr(response, "content") else str(response)
    parsed = parse_agent_json_output(raw)
    if parsed is not None:
        report = parsed.get("reasoning", parsed.get("reason", str(raw)[:300]))
        signal = parsed.get("signal", "N/A")
        logger.info(f"[market] → {signal}: {report[:80]}...")
    else:
        report = "市场分析暂时不可用"
        logger.warning("[market] 解析失败")

    return {"market_report": str(report), "messages": [response]}
