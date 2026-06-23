"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_preserves_text.py 文本保留
描述: 中文和 ASCII 文本不被误删
"""
from app.harness.emoji_clean import strip_emoji

def test_preserves_chinese():
    assert strip_emoji("突破阻力位") == "突破阻力位"

def test_preserves_ascii():
    assert strip_emoji("BUY signal confirmed") == "BUY signal confirmed"
