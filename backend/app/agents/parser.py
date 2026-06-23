"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: parser.py JSON解析与AgentReport转换
描述: 多层兜底解析器 — JSON → Markdown表格 → 正则KV → 返回结构化错误供调用方重试

包含:
- 函数: parse_agent_output — 从 LLM 原始输出中提取决策 dict（三层兜底）
- 函数: build_retry_prompt — 构造重试提示词（带错误反馈）
- 函数: agent_output_to_report — 将解析后的 JSON dict 转为 AgentReport 对象
"""

import json
import re

from app.schemas.agent import AgentReport, Confidence, Signal
from app.core.logger import get_logger

logger = get_logger()

# 有效信号值
_VALID_SIGNALS = {"BUY", "SELL", "HOLD"}
_VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}


# ---------------------------------------------------------------------------
# 字段归一化 — 防止 LLM 输出带后缀（如 "SELL (加仓做空)"）导致写库超长
# ---------------------------------------------------------------------------

# 信号归一化 — 从 LLM 输出中提取合法信号词，丢弃括号后缀等噪声。
# "SELL (加仓做空)" → "SELL"；"买" 之类非法值 → "HOLD"（安全默认）。
def _normalize_signal(val: str) -> str:
    """将 signal 字段归一化为 BUY/SELL/HOLD 之一。

    优先取首词大写；若不在合法集合，则尝试匹配字符串中包含的合法词；
    都不命中则返回 HOLD（安全默认，避免写库超长 + 避免误下单）。
    """
    if not val:
        return "HOLD"
    text = str(val).upper().strip()
    # 去掉常见 emoji 和括号后缀，取首词
    text = re.sub(r"[🟢🔴]", "", text)
    first_word = re.split(r"[\s(（\[【]", text, maxsplit=1)[0].strip()
    if first_word in _VALID_SIGNALS:
        return first_word
    # 首词不合法时，检查是否包含任一合法词（如 "强烈BUY"）
    for sig in _VALID_SIGNALS:
        if sig in text:
            return sig
    return "HOLD"


# 信心归一化 — 归一化为 HIGH/MEDIUM/LOW，非法值 → MEDIUM。
def _normalize_confidence(val: str) -> str:
    """将 confidence 字段归一化为 HIGH/MEDIUM/LOW 之一。"""
    if not val:
        return "MEDIUM"
    text = str(val).upper().strip()
    first_word = re.split(r"[\s(（\[【]", text, maxsplit=1)[0].strip()
    if first_word in _VALID_CONFIDENCE:
        return first_word
    for conf in _VALID_CONFIDENCE:
        if conf in text:
            return conf
    return "MEDIUM"


# ---------------------------------------------------------------------------
# 第 1 层: JSON 解析（花括号 + code fence + 尾逗号修复）
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> dict | None:
    """从文本中提取花括号包裹的 JSON 并解析。"""
    # 提取 code fence
    fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    # 提取花括号内容
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    text = text[start:end + 1]

    # 清理尾逗号
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    # 多策略尝试
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

    return None


# ---------------------------------------------------------------------------
# 第 2 层: Markdown 表格解析
# ---------------------------------------------------------------------------

def _parse_markdown_table(text: str) -> dict | None:
    """从 Markdown 表格中提取 key-value 对。

    支持格式:
      | 信号 | BUY |
      | **信号** | **BUY** |
      | 信号 | BUY | 备注 |
    """
    # 匹配表格行: | key | value | ... |
    rows = re.findall(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*(?:\|.*)?$", text, re.MULTILINE)
    if len(rows) < 2:
        return None

    result: dict = {}
    key_map = {
        "信号": "signal", "signal": "signal",
        "信心": "confidence", "confidence": "confidence",
        "仓位": "position_pct", "仓位%": "position_pct", "position_pct": "position_pct",
        "止损": "stop_loss", "stop loss": "stop_loss", "stop_loss": "stop_loss",
        "止盈": "take_profit", "take profit": "take_profit", "take_profit": "take_profit",
        "理由": "reason", "reason": "reason",
        "风险评级": "risk_rating", "risk_rating": "risk_rating",
        "风险": "risk_rating",
    }

    for key_raw, val_raw in rows:
        # 去掉 markdown 加粗标记
        key = re.sub(r"\*+", "", key_raw).strip().lower()
        val = re.sub(r"\*+", "", val_raw).strip()

        # 跳过分隔行
        if re.match(r"^[-:]+$", key) or not key:
            continue

        # 映射 key
        mapped = key_map.get(key)
        if not mapped:
            continue

        # 清理值
        if mapped == "signal":
            val = val.upper().replace("🟢", "").replace("🔴", "").strip()
        elif mapped == "confidence":
            val = val.upper().strip()
        elif mapped in ("position_pct", "stop_loss", "take_profit"):
            # 提取数字
            num_match = re.search(r"[\d.]+", str(val))
            val = num_match.group(0) if num_match else val

        result[mapped] = val

    return result if result else None


# ---------------------------------------------------------------------------
# 第 3 层: 正则 key-value 提取
# ---------------------------------------------------------------------------

def _parse_kv_text(text: str) -> dict | None:
    """用正则从自由文本中提取 key: value 或 key=value 对。

    支持格式:
      signal: BUY
      **signal**: BUY
      signal=BUY
      "signal": "BUY"
    """
    patterns = [
        # JSON-like: "signal": "BUY"
        (r'"?(signal|confidence|position_pct|stop_loss|take_profit|reason|risk_rating)"?\s*:\s*"?(.+?)"?(?:,|\n|$)', False),
        # Markdown bold: **signal**: BUY
        (r'\*{0,2}(signal|confidence|position_pct|stop_loss|take_profit|reason|risk_rating)\*{0,2}\s*[:=]\s*(.+?)(?:\n|$)', False),
    ]

    result: dict = {}
    text_lower = text.lower()

    for pattern, _ in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for key, val in matches:
            key_lower = key.lower()
            val = val.strip().rstrip(',').strip('"').strip("'")

            if key_lower == "signal":
                val = val.upper().replace("🟢", "").replace("🔴", "").strip()
                if val not in _VALID_SIGNALS:
                    continue
            elif key_lower == "confidence":
                val = val.upper().strip()
                if val not in _VALID_CONFIDENCE:
                    continue
            elif key_lower in ("position_pct", "stop_loss", "take_profit"):
                num_match = re.search(r"[\d.]+", val)
                val = num_match.group(0) if num_match else val

            if key_lower not in result:
                result[key_lower] = val

    return result if result else None


# ---------------------------------------------------------------------------
# 汇总: 三层兜底解析
# ---------------------------------------------------------------------------

class ParseResult:
    """解析结果 — 成功时 data 包含决策 dict，失败时 error 包含错误描述。"""
    def __init__(self, data: dict | None, error: str = "", strategy: str = ""):
        self.data = data or {}
        self.success = data is not None and len(data) > 0
        self.error = error
        self.strategy = strategy  # "json" / "table" / "kv"


# 解析结果归一化 — 三层解析统一过一遍，确保 signal/confidence 合法。
# 防止 LLM 输出 "SELL (加仓做空)" 带后缀导致写库 String(10) 超长崩溃。
def _finalize_parsed(parsed: dict) -> dict:
    """对解析后的 dict 归一化 signal/confidence 字段，返回新 dict。"""
    if "signal" in parsed:
        parsed["signal"] = _normalize_signal(parsed["signal"])
    if "confidence" in parsed:
        parsed["confidence"] = _normalize_confidence(parsed["confidence"])
    return parsed


def parse_agent_output(raw: str) -> ParseResult:
    """三层兜底解析 LLM 输出：JSON → Markdown 表格 → 正则 KV。

    返回 ParseResult，调用方根据 .success 决定是否需要重试。
    """
    if not raw or not raw.strip():
        return ParseResult(None, error="输出为空", strategy="none")

    text = raw.strip()

    # 第 1 层: JSON
    parsed = _parse_json(text)
    if parsed:
        parsed = _finalize_parsed(parsed)
        logger.info(f"解析成功 (JSON): signal={parsed.get('signal', '?')}")
        return ParseResult(parsed, strategy="json")

    # 第 2 层: Markdown 表格
    parsed = _parse_markdown_table(text)
    if parsed:
        parsed = _finalize_parsed(parsed)
        logger.info(f"解析成功 (Markdown表格): signal={parsed.get('signal', '?')}")
        return ParseResult(parsed, strategy="table")

    # 第 3 层: 正则 KV
    parsed = _parse_kv_text(text)
    if parsed:
        parsed = _finalize_parsed(parsed)
        logger.info(f"解析成功 (正则KV): signal={parsed.get('signal', '?')}")
        return ParseResult(parsed, strategy="kv")

    # 全部失败
    logger.warning(f"三层解析均失败, raw={text[:300]}")
    return ParseResult(
        None,
        error=(
            "你的上一条输出格式不符合要求。请严格按照 JSON 格式输出最终决策，"
            "例如: {\"signal\": \"BUY\", \"confidence\": \"HIGH\", "
            "\"position_pct\": 30, \"stop_loss\": 0.086, \"take_profit\": 0.089, "
            "\"reason\": \"RSI超卖+布林带下轨\", \"risk_rating\": \"MEDIUM\"}\n"
            "注意: 1) 必须用花括号 {} 包裹 2) 所有 key 用双引号 3) 数值不加引号"
        ),
        strategy="none",
    )


# ---------------------------------------------------------------------------
# 重试提示词构造
# ---------------------------------------------------------------------------

def build_retry_prompt(original_output: str, parse_error: str) -> str:
    """构造带错误反馈的重试提示词，要求模型重新输出 JSON。"""
    return (
        f"你上一次输出了以下内容:\n---\n{original_output[:800]}\n---\n"
        f"但解析器无法从中提取决策数据，原因: {parse_error}\n\n"
        f"请重新输出最终的交易决策，必须使用严格的 JSON 格式，放在花括号内:\n"
        f'{{"signal": "BUY或SELL或HOLD", "confidence": "HIGH或MEDIUM或LOW", '
        f'"position_pct": 数字(0-100), "stop_loss": 数字, "take_profit": 数字, '
        f'"reason": "决策理由", "risk_rating": "LOW或MEDIUM或HIGH或EXTREME"}}'
    )


# ---------------------------------------------------------------------------
# AgentReport 转换（保持原有接口兼容）
# ---------------------------------------------------------------------------

def parse_agent_json_output(raw: str) -> dict | None:
    """兼容旧接口：三层兜底解析，返回 dict 或 None。"""
    result = parse_agent_output(raw)
    return result.data if result.success else None


def agent_output_to_report(parsed: dict | None, role_name: str) -> AgentReport:
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
