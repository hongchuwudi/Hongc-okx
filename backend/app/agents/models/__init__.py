"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: __init__.py 模型模块导出
描述: 5 个 Agent LLM 模型实例汇总导出
"""

import os

# 禁用 langchain-openai 的自定义 TCP keepalive transport，
# 恢复 httpx 原生代理行为，消除 "injected a custom httpx transport" 警告
os.environ.setdefault("LANGCHAIN_OPENAI_TCP_KEEPALIVE", "0")

from app.agents.models.model_scheduler import get_scheduler_llm
from app.agents.models.model_analyst import get_analyst_llm
from app.agents.models.model_reviewer import get_reviewer_llm
from app.agents.models.model_risk import get_risk_llm
from app.agents.models.model_trader import get_trader_llm
from app.agents.models.model_super_analyst import get_super_analyst_llm
from app.agents.models.model_solo import get_solo_llm
