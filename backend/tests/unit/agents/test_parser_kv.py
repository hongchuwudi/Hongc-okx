"""
测试: AI 输出正则 key-value 解析（第 3 层兜底）
"""

from app.agents.parser import parse_agent_output


def test_kv_colon_format():
    """signal: BUY 冒号格式。"""
    raw = "signal: BUY\nconfidence: HIGH\nstop_loss: 97.0\ntake_profit: 105.0\nreason: 测试"
    result = parse_agent_output(raw)
    assert result.success
    assert result.strategy == "kv"
    assert result.data["signal"] == "BUY"


def test_kv_json_like():
    """"key": "value" JSON-like 格式但没花括号。"""
    raw = '"signal": "BUY",\n"confidence": "HIGH",\n"stop_loss": "97.0"'
    result = parse_agent_output(raw)
    assert result.success
