"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: conftest.py tick_strategy 单元测试公共夹具
描述: mock 余额检查，让 agent 路径单元测试不依赖真实 DeepSeek 网络

tick_analyze_strategy 在 use_multi_agent=True 时会先查 DeepSeek 余额，
余额不足则降级。单元测试测的是 agent 路径本身，不应被真实余额干扰，
也不应依赖外部网络。autouse fixture 默认让余额充足，走 agent 路径。

需要测降级的用例可自行覆盖 patch。
"""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def mock_balance_sufficient():
    """默认 mock 余额充足，agent 路径测试不受真实 DeepSeek 影响。"""
    with patch(
        "app.services.agent.agent_balance_service.check_balance_sufficient",
        new=AsyncMock(return_value=(True, 100.0)),
    ):
        yield
