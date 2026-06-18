"""
测试: AI 输出 JSON 格式解析（第 1 层兜底）
"""

from app.agents.parser import parse_agent_output


def test_plain_json():
    """标准 JSON 直接解析。"""
    raw = '{"signal": "BUY", "confidence": "HIGH", "position_pct": 50, "stop_loss": 97.0, "take_profit": 105.0, "reason": "金叉"}'
    result = parse_agent_output(raw)
    assert result.success
    assert result.strategy == "json"
    assert result.data["signal"] == "BUY"


def test_json_in_code_fence():
    """```json ... ``` 包裹的 JSON。"""
    raw = '```json\n{"signal": "SELL", "confidence": "MEDIUM", "position_pct": 30, "stop_loss": 102.0, "take_profit": 95.0, "reason": "死叉"}\n```'
    result = parse_agent_output(raw)
    assert result.success
    assert result.data["signal"] == "SELL"


def test_json_with_trailing_comma():
    """JSON 末尾多余逗号自动修复。"""
    raw = '{"signal": "HOLD", "confidence": "LOW", "position_pct": 0, "stop_loss": 98.0, "take_profit": 102.0, "reason": "观望",}'
    result = parse_agent_output(raw)
    assert result.success


def test_json_embedded_in_text():
    """JSON 嵌在自然语言中，提取花括号部分。"""
    raw = '分析: 市场趋势向上。决策: {"signal": "BUY", "confidence": "HIGH", "position_pct": 60, "stop_loss": 96.5, "take_profit": 106.0, "reason": "趋势确认"}'
    result = parse_agent_output(raw)
    assert result.success
    assert result.data["signal"] == "BUY"
