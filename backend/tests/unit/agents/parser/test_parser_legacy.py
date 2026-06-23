"""
测试: parse_agent_json_output 旧接口 + agent_output_to_report 转换
"""

from app.agents.parser import parse_agent_json_output, agent_output_to_report


def test_legacy_json_success():
    """旧接口成功返回 dict。"""
    data = parse_agent_json_output(
        '{"signal": "BUY", "confidence": "HIGH", "position_pct": 50, '
        '"stop_loss": 97.0, "take_profit": 105.0, "reason": "test"}'
    )
    assert data is not None
    assert data["signal"] == "BUY"


def test_legacy_json_failure():
    """旧接口失败返回 None。"""
    data = parse_agent_json_output("无效")
    assert data is None


def test_report_valid():
    """正常 dict 转 AgentReport。"""
    parsed = {"signal": "BUY", "confidence": "HIGH", "reason": "测试",
              "stop_loss": 97.0, "take_profit": 105.0, "position_pct": 50}
    report = agent_output_to_report(parsed, "analyst")
    assert str(report.signal) == "Signal.BUY"
    assert report.sl == 97.0
    assert report.position_pct == 50


def test_report_none_input():
    """None 输入返回不可用提示。"""
    report = agent_output_to_report(None, "analyst")
    assert "不可用" in report.reasoning


def test_report_invalid_signal():
    """非法 signal 兜底为 HOLD。"""
    parsed = {"signal": "INVALID", "confidence": "HIGH"}
    report = agent_output_to_report(parsed, "analyst")
    assert str(report.signal) == "Signal.HOLD"
