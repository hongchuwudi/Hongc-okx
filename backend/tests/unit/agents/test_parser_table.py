"""
测试: AI 输出 Markdown 表格解析（第 2 层兜底）
"""

from app.agents.parser import parse_agent_output


def test_markdown_table():
    """| 信号 | BUY | 标准表格。"""
    raw = """| 信号 | BUY |
| 信心 | HIGH |
| 仓位 | 50 |
| 止损 | 97.0 |
| 止盈 | 105.0 |
| 理由 | 金叉确认 |"""
    result = parse_agent_output(raw)
    assert result.success
    assert result.strategy == "table"
    assert result.data["signal"] == "BUY"


def test_markdown_bold_table():
    """加粗标记 **key** | **value**。"""
    raw = """| **信号** | **SELL** |
| **信心** | **MEDIUM** |
| **止损** | **102.0** |
| **止盈** | **95.0** |
| **理由** | **死叉信号** |"""
    result = parse_agent_output(raw)
    assert result.success
    assert result.data["signal"] == "SELL"
