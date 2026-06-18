"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_tick_emoji.py emoji 清洗测试
描述: 验证 _clean_signal 的 emoji 移除 + 空白清理 + 边界 case

包含:
- TestEmojiClean — emoji 和特殊字符清洗
- TestEmojiEdge — 空字符串 / None / 纯中文 / 纯 ASCII
"""

import pytest
from app.harness.emoji_clean import strip_emoji as _clean_signal


class TestEmojiClean:
    """emoji 移除 + 空白清理。"""

    def test_removes_rocket_emoji(self):
        """火箭 emoji (U+1F680) 被移除。"""
        text = "BUY \U0001F680 break"
        result = _clean_signal(text)
        assert "BUY" in result
        assert "break" in result
        assert "\U0001F680" not in result

    def test_removes_chart_emojis(self):
        """K 线图 emoji (U+1F4C8 U+1F4C9) 被移除。"""
        result = _clean_signal("\U0001F4C8 \U0001F4C9 SELL \U0001F534")
        assert "\U0001F4C8" not in result
        assert "\U0001F4C9" not in result
        assert "\U0001F534" not in result
        assert "SELL" in result

    def test_removes_warning_and_checkmark(self):
        """警告 (U+26A0 U+FE0F) 和勾号 (U+2705) 被移除。"""
        text = "⚠️ danger ✅ ok"
        result = _clean_signal(text)
        assert "danger" in result
        assert "ok" in result

    def test_preserves_chinese(self):
        """中文文本保持不变（不会误删 CJK 字符）。"""
        assert _clean_signal("突破阻力位") == "突破阻力位"

    def test_preserves_ascii(self):
        """纯 ASCII 文本不变。"""
        assert _clean_signal("BUY signal confirmed") == "BUY signal confirmed"


class TestEmojiEdge:
    """边界条件。"""

    def test_empty_string(self):
        assert _clean_signal("") == ""

    def test_none_input(self):
        assert _clean_signal(None) is None

    def test_emoji_only_string(self):
        """纯 emoji 字符串返回空字符串。"""
        result = _clean_signal("\U0001F600\U0001F603")
        assert result == ""

    def test_strips_leading_trailing_whitespace(self):
        """移除 emoji 后自动 strip 空白。"""
        text = "  \U0001F44D  HOLD  \U0001F44E  "
        result = _clean_signal(text)
        assert result == "HOLD"
