"""
测试: 三层解析全部失败时的兜底行为
"""

from app.agents.parser import parse_agent_output, build_retry_prompt


def test_empty_input():
    """空字符串返回失败。"""
    result = parse_agent_output("")
    assert not result.success
    assert result.strategy == "none"


def test_noise_text():
    """纯噪音文本无法解析。"""
    result = parse_agent_output("今天天气不错，适合交易")
    assert not result.success


def test_invalid_json_no_braces():
    """没有花括号的纯文本返回失败并带错误信息。"""
    result = parse_agent_output("signal BUY confidence HIGH")
    assert not result.success
    assert result.error != ""


def test_retry_prompt_generated():
    """解析失败后 build_retry_prompt 生成重试提示词。"""
    result = parse_agent_output("无效文本")
    assert not result.success
    retry = build_retry_prompt("无效文本", result.error)
    assert "JSON" in retry
    assert "无效文本" in retry
