"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_emoji.py emoji 清洗工具
描述: 移除 AI 输出中的 emoji，防止 GBK 编码崩溃和前端显示异常
        实际逻辑已迁移至 app.core.emoji_clean，此模块保留向后兼容。

包含:
- 函数: _clean_signal — 委托到 app.core.emoji_clean.strip_emoji
"""

from app.harness.emoji_clean import strip_emoji as _clean_signal
