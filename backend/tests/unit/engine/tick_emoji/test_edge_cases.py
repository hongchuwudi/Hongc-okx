"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_edge_cases.py 边界情况
描述: 空字符串/None/纯emoji/前后空白
"""
from app.harness.emoji_clean import strip_emoji

def test_empty_string():
    assert strip_emoji("") == ""

def test_none_input():
    assert strip_emoji(None) is None

def test_emoji_only_returns_empty():
    assert strip_emoji("😀😃") == ""

def test_strips_whitespace():
    assert strip_emoji("  👍  HOLD  👎  ") == "HOLD"
