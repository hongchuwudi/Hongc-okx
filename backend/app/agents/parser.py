"""集中式 JSON 解析器 + AgentReport 转换

全项目唯一 JSON 解析入口。
处理：code fence、尾逗号、单引号、破损 Unicode。
"""

import json
import re

from app.agents.schemas import AgentReport, Confidence, Signal
from app.logger import get_logger

logger = get_logger()


def parse_agent_json_output(raw: str) -> dict | None:
    """从 LLM 原始输出中提取 JSON dict。"""
    if not raw:
        return None

    text = raw.strip()

    # 1. 提取 code fence
    fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    # 2. 提取花括号
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        logger.warning(f"JSON 解析: 未找到花括号, raw={raw[:200]}")
        return None
    text = text[start:end + 1]

    # 3. 清理尾逗号
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    # 4-7. 多策略尝试
    for attempt in [
        lambda t: json.loads(t),
        lambda t: json.loads(t.replace("'", '"')),
        lambda t: json.loads(re.sub(r'(\w+):', r'"\1":', t)),
        lambda t: json.loads(t.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')),
    ]:
        try:
            return attempt(text)
        except (json.JSONDecodeError, UnicodeError):
            continue

    logger.warning(f"JSON 解析完全失败: {raw[:300]}")
    return None


def agent_output_to_report(parsed: dict | None, role_name: str) -> AgentReport:
    """将解析的 JSON dict 转为 AgentReport。"""
    if parsed is None:
        return AgentReport(reasoning=f"{role_name} 分析不可用")

    signal = str(parsed.get("signal", "HOLD")).upper().strip()
    if signal not in ("BUY", "SELL", "HOLD"):
        signal = "HOLD"

    conf = str(parsed.get("confidence", "MEDIUM")).upper().strip()
    if conf not in ("HIGH", "MEDIUM", "LOW"):
        conf = "MEDIUM"

    return AgentReport(
        signal=Signal(signal),
        confidence=Confidence(conf),
        reasoning=str(parsed.get("reasoning", parsed.get("reason", "")))[:300],
        sl=float(parsed.get("sl", parsed.get("stop_loss", 0)) or 0),
        tp=float(parsed.get("tp", parsed.get("take_profit", 0)) or 0),
        position_pct=max(0, min(100, float(parsed.get("position_pct", 0) or 0))),
    )
