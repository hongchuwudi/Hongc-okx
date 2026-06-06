"""所有 Agent 提示词汇总导出"""

from app.agents.prompts.supervisor import SUPERVISOR_SYSTEM
from app.agents.prompts.market import MARKET_SYSTEM
from app.agents.prompts.risk import RISK_SYSTEM
from app.agents.prompts.memory import MEMORY_SYSTEM
from app.agents.prompts.trader import TRADER_SYSTEM

# 给 Worker 节点使用的提示词字典
WORKER_PROMPTS = {
    "market": MARKET_SYSTEM,
    "risk": RISK_SYSTEM,
    "memory": MEMORY_SYSTEM,
}

__all__ = [
    "SUPERVISOR_SYSTEM",
    "MARKET_SYSTEM",
    "RISK_SYSTEM",
    "MEMORY_SYSTEM",
    "TRADER_SYSTEM",
    "WORKER_PROMPTS",
]
