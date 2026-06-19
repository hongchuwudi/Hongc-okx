"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: harness/emoji_clean.py emoji 清洗工具
描述: 公共胶水层 — 移除字符串中的 emoji，防止 GBK 编码崩溃和前端显示异常
      供 engine/loop/tick_emoji 和 agents/status/agent_status_persist 共享

包含:
- 常量: _EMOJI_RE — 匹配全部 Unicode emoji 的正则
- 函数: strip_emoji — 移除 emoji 并清理空白
"""

import re

_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # 表情符号
    "\U0001F300-\U0001F5FF"  # 符号和象形文字
    "\U0001F680-\U0001F6FF"  # 交通和地图
    "\U0001F1E0-\U0001F1FF"  # 旗帜
    "\U00002702-\U000027B0"  # 装饰符号
    "\U000024C2"              # 圆圈M
    "\U0001F250-\U0001F251"  # 带圈汉字
    "\U0001F900-\U0001F9FF"  # 补充符号
    "\U0001FA00-\U0001FA6F"  # 棋牌
    "\U0001FA70-\U0001FAFF"  # 扩展-A
    "\U00002600-\U000026FF"  # 杂项符号
    "\U0000FE00-\U0000FE0F"  # 变体选择器
    "\U0000200D"              # 零宽连字符
    "\U000020E3"              # 组合用封闭键帽
    "]+",
    re.UNICODE,
)


def strip_emoji(text: str) -> str:
    """移除字符串中所有 emoji 字符，合并多余空格并 strip 首尾空白。"""
    if not text:
        return text
    cleaned = _EMOJI_RE.sub("", text)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()
