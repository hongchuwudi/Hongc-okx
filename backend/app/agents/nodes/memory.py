"""历史复盘节点"""

from app.agents.shared import SupervisorState
from app.agents.parser import parse_agent_json_output
from app.agents.prompts.memory import MEMORY_SYSTEM
from app.agents.shared import get_llm
from app.logger import get_logger

logger = get_logger()


def memory_node(state: SupervisorState) -> dict:
    llm = get_llm()
    logger.info("[memory] 启动复盘分析...")

    response = llm.invoke([
        {"role": "system", "content": MEMORY_SYSTEM},
        {"role": "user", "content": f"{state['memory_text']}\n\n{state['position_text']}\n\n请输出你的分析（严格 JSON）。"},
    ])
    raw = response.content if hasattr(response, "content") else str(response)
    parsed = parse_agent_json_output(raw)
    if parsed is not None:
        report = parsed.get("reasoning", parsed.get("reason", str(raw)[:300]))
        logger.info(f"[memory] → {report[:80]}...")
    else:
        report = "复盘分析暂时不可用"
        logger.warning("[memory] 解析失败")

    return {"memory_report": str(report), "messages": [response]}
