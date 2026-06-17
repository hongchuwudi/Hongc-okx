"""
创建时间: 2026-06-16
作者: hongchuwudi
文件名: runtime/ 运行时配置热切换
描述: 从 Redis 读取配置并即时生效，无需重启引擎

目录结构:
- mixin.py              — RuntimeSyncMixin + _sync_runtime() 编排器
- runtime_agent_mode.py — Agent 模式热切换
- runtime_prompt.py     — 提示词热重载
- runtime_symbol.py     — 交易对热切换
- runtime_leverage.py   — 杠杆热切换
- runtime_interval.py   — Tick 间隔热切换
"""

from app.engine.runtime.mixin import RuntimeSyncMixin
