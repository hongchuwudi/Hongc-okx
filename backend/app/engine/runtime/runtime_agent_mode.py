"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: runtime_agent_mode.py Agent 模式热切换
描述: 根据 Redis 配置热切换 Agent 模式（tech / 1_agent / 3_agent / 5_agent）

包含:
- 函数: _sync_agent_mode — 读取 agent_mode 并切换 coordinator
"""

from app.services.agent.agent_coordinator_service import (
    create_coordinator, create_coordinator_3, create_coordinator_solo,
)
from app.services.config.runtime import get_runtime_async
from app.core.logger import get_logger

logger = get_logger()


async def _sync_agent_mode(engine) -> None:
    """读取 Redis agent_mode，变化时热切换 coordinator。"""
    mode = await get_runtime_async("agent_mode")
    if mode == engine._last_mode and engine.coordinator is not None:
        return

    engine._last_mode = mode
    if mode == "tech":
        engine.use_multi_agent = False
        engine.agent_mode_display = "技术指标 (纯规则)"
        engine.coordinator = None
        logger.info("[运行时] 切换模式 -> 技术指标")
    elif mode == "1_agent":
        engine.coordinator = create_coordinator_solo()
        engine.use_multi_agent = True
        engine.agent_mode_display = "1 Agent Solo (急速)"
        logger.info("[运行时] 切换模式 -> 1 Agent Solo")
    elif mode == "3_agent":
        engine.coordinator = create_coordinator_3()
        engine.use_multi_agent = True
        engine.agent_mode_display = "3 Agent Swarm (快速)"
        logger.info("[运行时] 切换模式 -> 3 Agent")
    else:
        engine.coordinator = create_coordinator()
        engine.use_multi_agent = True
        engine.agent_mode_display = "5 Agent Swarm (完整)"
        logger.info("[运行时] 切换模式 -> 5 Agent")
