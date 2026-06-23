"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_parser_normalize.py signal/confidence 归一化
描述: 钉住 parser 归一化行为 — LLM 输出带后缀时提取合法词，防写库超长崩溃

回归背景: LLM 输出 "SELL (加仓做空)" 原样写入 TradeMemory.signal(String(10))
导致 StringDataRightTruncation 写库崩溃。parser 现在统一归一化。

包含:
- 函数: test_normalize_signal_* — signal 归一化各种输入
- 函数: test_normalize_confidence_* — confidence 归一化
- 函数: test_parse_*_with_suffix — 三层解析带后缀输入归一化
"""
from app.agents.parser import (
    _normalize_signal,
    _normalize_confidence,
    parse_agent_output,
)


# ═══════════════════════════════════════════════════════════════
# signal 归一化
# ═══════════════════════════════════════════════════════════════

def test_normalize_signal_plain():
    assert _normalize_signal("BUY") == "BUY"
    assert _normalize_signal("SELL") == "SELL"
    assert _normalize_signal("HOLD") == "HOLD"


def test_normalize_signal_with_paren_suffix():
    """带括号后缀 → 取首词。这是崩溃 bug 的核心回归。"""
    assert _normalize_signal("SELL (加仓做空)") == "SELL"
    assert _normalize_signal("BUY (突破追多)") == "BUY"
    assert _normalize_signal("HOLD (观望)") == "HOLD"


def test_normalize_signal_lowercase():
    assert _normalize_signal("buy") == "BUY"
    assert _normalize_signal("sell") == "SELL"


def test_normalize_signal_with_emoji():
    """带 emoji → 去掉后取首词。"""
    assert _normalize_signal("🟢BUY") == "BUY"
    assert _normalize_signal("SELL🔴") == "SELL"


def test_normalize_signal_embedded():
    """合法词嵌在字符串中 → 匹配包含。"""
    assert _normalize_signal("strong SELL") == "SELL"
    assert _normalize_signal("趋势BUY确认") == "BUY"


def test_normalize_signal_invalid_defaults_hold():
    """非法值 → HOLD（安全默认，避免误下单）。"""
    assert _normalize_signal("买") == "HOLD"
    assert _normalize_signal("观望") == "HOLD"
    assert _normalize_signal("xyz") == "HOLD"
    assert _normalize_signal("") == "HOLD"
    assert _normalize_signal(None) == "HOLD"


def test_normalize_signal_length_safe():
    """归一化结果长度 <= 4（BUY/SELL/HOLD），永不超 String(10)。"""
    for val in ["SELL (加仓做空)", "BUY (突破追多加仓)", "HOLD (继续观望不动)"]:
        result = _normalize_signal(val)
        assert len(result) <= 4, f"{val} -> {result} 长度 {len(result)} > 4"


# ═══════════════════════════════════════════════════════════════
# confidence 归一化
# ═══════════════════════════════════════════════════════════════

def test_normalize_confidence_plain():
    assert _normalize_confidence("HIGH") == "HIGH"
    assert _normalize_confidence("MEDIUM") == "MEDIUM"
    assert _normalize_confidence("LOW") == "LOW"


def test_normalize_confidence_with_suffix():
    assert _normalize_confidence("MEDIUM (一般)") == "MEDIUM"
    assert _normalize_confidence("HIGH (高)") == "HIGH"


def test_normalize_confidence_invalid_defaults_medium():
    assert _normalize_confidence("高") == "MEDIUM"
    assert _normalize_confidence("") == "MEDIUM"
    assert _normalize_confidence(None) == "MEDIUM"


# ═══════════════════════════════════════════════════════════════
# 三层解析带后缀归一化（端到端）
# ═══════════════════════════════════════════════════════════════

def test_parse_json_with_signal_suffix_normalized():
    """JSON 层: signal 带括号后缀 → 归一化为 SELL。"""
    raw = '{"signal": "SELL (加仓做空)", "confidence": "MEDIUM", "reason": "test"}'
    result = parse_agent_output(raw)
    assert result.success
    assert result.data["signal"] == "SELL"
    assert result.data["confidence"] == "MEDIUM"


def test_parse_table_with_signal_suffix_normalized():
    """Markdown 表格层: signal 带括号后缀 → 归一化。"""
    raw = "| 信号 | SELL (加仓做空) |\n| 信心 | MEDIUM |"
    result = parse_agent_output(raw)
    assert result.success
    assert result.data["signal"] == "SELL"


def test_parse_result_signal_never_exceeds_10_chars():
    """解析结果 signal 长度永不超 10（TradeMemory.signal 字段上限）。"""
    cases = [
        '{"signal": "SELL (加仓做空扩大战果)", "confidence": "HIGH"}',
        "| 信号 | BUY (趋势突破强烈追多) |\n| 信心 | HIGH |",
        '{"signal": "HOLD (继续观望不动等信号)", "confidence": "LOW"}',
    ]
    for raw in cases:
        result = parse_agent_output(raw)
        assert result.success, f"应解析成功: {raw}"
        assert len(result.data["signal"]) <= 10, (
            f"signal={result.data['signal']!r} 超过 10 字符，会写库崩溃"
        )
        assert result.data["signal"] in ("BUY", "SELL", "HOLD")
