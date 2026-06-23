"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_ai_balance_api.py DeepSeek 余额查询 API 集成测试
描述: GET /api/v1/config/ai-balance 端点 — FastAPI TestClient + mock service

验证:
- 端点路由可达，返回 DeepSeekBalanceResponse 结构
- 正常余额时 degraded=False
- 欠费余额时 degraded=True
- degrade_threshold 字段正确反映服务层阈值

不依赖真实 DeepSeek 网络，mock agent_balance_service.get_deepseek_balance。
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient，session 级共享 app 实例。"""
    from app.api.main import app
    return TestClient(app)


def _mock_balance_return(total: float, available: bool) -> dict:
    """构造 get_deepseek_balance 的标准化返回。"""
    return {
        "is_available": available,
        "total_balance": total,
        "currency": "CNY",
        "granted_balance": 0.0,
        "topped_up_balance": total,
        "raw": {},
    }


class TestAiBalanceEndpoint:
    """GET /api/v1/config/ai-balance 端点测试。"""

    def test_endpoint_returns_200(self, client):
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance",
            return_value=_mock_balance_return(10.0, True),
        ):
            r = client.get("/api/v1/config/ai-balance")
        assert r.status_code == 200

    def test_response_has_all_fields(self, client):
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance",
            return_value=_mock_balance_return(10.0, True),
        ):
            body = client.get("/api/v1/config/ai-balance").json()

        for key in ("is_available", "total_balance", "currency",
                    "granted_balance", "topped_up_balance",
                    "degrade_threshold", "degraded"):
            assert key in body, f"缺少字段: {key}"

    def test_normal_balance_not_degraded(self, client):
        """正常余额（>= 阈值）时 degraded=False。"""
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance",
            return_value=_mock_balance_return(10.0, True),
        ):
            body = client.get("/api/v1/config/ai-balance").json()
        assert body["is_available"] is True
        assert body["total_balance"] == 10.0
        assert body["degraded"] is False

    def test_overdraft_balance_degraded(self, client):
        """欠费（负余额 < 阈值）时 degraded=True。"""
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance",
            return_value=_mock_balance_return(-0.10, False),
        ):
            body = client.get("/api/v1/config/ai-balance").json()
        assert body["is_available"] is False
        assert body["total_balance"] == -0.10
        assert body["degraded"] is True

    def test_degrade_threshold_matches_service(self, client):
        """端点返回的 degrade_threshold 应等于服务层常量。"""
        from app.services.agent.agent_balance_service import BALANCE_DEGRADE_THRESHOLD
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance",
            return_value=_mock_balance_return(10.0, True),
        ):
            body = client.get("/api/v1/config/ai-balance").json()
        assert body["degrade_threshold"] == BALANCE_DEGRADE_THRESHOLD

    def test_low_balance_below_threshold_degraded(self, client):
        """余额 0.01 < 0.05 阈值时 degraded=True。"""
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance",
            return_value=_mock_balance_return(0.01, True),
        ):
            body = client.get("/api/v1/config/ai-balance").json()
        assert body["degraded"] is True
