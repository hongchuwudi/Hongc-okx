"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: parser.py JSON解析与AgentReport转换
描述: 集中式 JSON 解析器 + AgentReport 转换，全项目唯一 JSON 解析入口

包含:
- 函数: parse_agent_json_output — 从 LLM 原始输出中提取并解析 JSON dict
- 函数: agent_output_to_report — 将解析后的 JSON dict 转为 AgentReport 对象
"""

import json
import re

from app.agents.schemas import AgentReport, Confidence, Signal
from app.logger import get_logger

# 全局日志记录器
logger = get_logger()


def parse_agent_json_output(raw: str) -> dict | None:
    """从 LLM 原始输出中提取 JSON dict。

    处理：code fence、尾逗号、单引号、破损 Unicode、多种 JSON 解析策略。
    """
    if not raw:
        return None

    text = raw.strip()

    # 1. 提取 code fence（```json ... ``` 或 ``` ... ```）
    fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    # 2. 提取花括号内容
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        logger.warning(f"JSON 解析: 未找到花括号, raw={raw[:200]}")
        return None
    text = text[start:end + 1]

    # 3. 清理尾逗号（如 {a:1,} 或 [1,]）
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    # 4-7. 多策略尝试解析（从标准到宽松）
    for attempt in [
        lambda t: json.loads(t),  # 标准 JSON
        lambda t: json.loads(t.replace("'", '"')),  # 替换单引号为双引号
        lambda t: json.loads(re.sub(r'(\w+):', r'"\1":', t)),  # 给键名加引号
        lambda t: json.loads(t.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')),  # 修复 Unicode
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

    # 提取并验证信号
    signal = str(parsed.get("signal", "HOLD")).upper().strip()
    if signal not in ("BUY", "SELL", "HOLD"):
        signal = "HOLD"

    # 提取并验证置信度
    conf = str(parsed.get("confidence", "MEDIUM")).upper().strip()
    if conf not in ("HIGH", "MEDIUM", "LOW"):
        conf = "MEDIUM"

    return AgentReport(
        signal=Signal(signal),  # 交易信号
        confidence=Confidence(conf),  # 置信度
        reasoning=str(parsed.get("reasoning", parsed.get("reason", "")))[:300],  # 分析理由
        sl=float(parsed.get("sl", parsed.get("stop_loss", 0)) or 0),  # 止损价
        tp=float(parsed.get("tp", parsed.get("take_profit", 0)) or 0),  # 止盈价
        position_pct=max(0, min(100, float(parsed.get("position_pct", 0) or 0))),  # 仓位百分比
    )
