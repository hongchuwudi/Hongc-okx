"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_removes_emojis.py emoji 移除
描述: 火箭/K线/警告/勾号 emoji 被正确移除
"""
from app.harness.emoji_clean import strip_emoji

def test_removes_rocket():
    result = strip_emoji("BUY 🚀 break")
    assert "BUY" in result and "break" in result
    assert "🚀" not in result

def test_removes_chart_emojis():
    result = strip_emoji("📈 📉 SELL")
    assert "📈" not in result and "📉" not in result
    assert "SELL" in result

def test_removes_warning_checkmark():
    result = strip_emoji("⚠️ danger ✅ ok")
    assert "danger" in result and "ok" in result
