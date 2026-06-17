"""
创建时间: 2026-06-16
作者: hongchuwudi
文件名: mixin.py 运行时同步混入类
描述: RuntimeSyncMixin — _sync_runtime() 编排器，调用 5 个子步骤

目录结构:
- runtime_agent_mode.py — Agent 模式热切换
- runtime_prompt.py    — 提示词热重载
- runtime_symbol.py    — 交易对热切换
- runtime_leverage.py  — 杠杆热切换
- runtime_interval.py  — Tick 间隔热切换

包含:
- 类: RuntimeSyncMixin — 运行时配置热切换混入类
"""

from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
from app.engine.runtime.runtime_prompt import _sync_prompt
from app.engine.runtime.runtime_symbol import _sync_symbol
from app.engine.runtime.runtime_leverage import _sync_leverage
from app.engine.runtime.runtime_interval import _sync_interval


class RuntimeSyncMixin:
    """混入类 — 提供 _sync_runtime() 方法，供 TradingEngine 继承。

    要求宿主类 __init__ 中必须初始化以下属性：
    - self._last_mode, self._last_symbol, self._last_leverage, self._last_prompt_version
    - self.use_multi_agent, self.agent_mode_display, self.coordinator
    - self.exchange, self.market_data, self.scheduler
    - self._symbol, self.position_manager
    """

    async def _sync_runtime(self) -> None:
        """读取 Redis 运行时配置，逐项检测变化并热切换。"""
        await _sync_agent_mode(self)
        await _sync_prompt(self)
        await _sync_symbol(self)
        await _sync_leverage(self)
        await _sync_interval(self)
