"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_agent_balance_service.py DeepSeek 余额查询服务单元测试
描述: mock httpx 响应，验证余额标准化逻辑 + 容错降级判断

不依赖真实网络，全部用 mock。

包含:
- class TestGetDeepSeekBalance — 余额接口返回标准化
- class TestCheckBalanceSufficient — 降级判断 + 容错
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.agent.agent_balance_service import (
    get_deepseek_balance,
    check_balance_sufficient,
    BALANCE_DEGRADE_THRESHOLD,
)


# 模拟 DeepSeek 余额接口原始返回
_NORMAL_RAW = {
    "is_available": True,
    "balance_infos": [{
        "currency": "CNY",
        "total_balance": "10.50",
        "granted_balance": "5.00",
        "topped_up_balance": "5.50",
    }],
}

_OVERDRAFT_RAW = {
    "is_available": False,
    "balance_infos": [{
        "currency": "CNY",
        "total_balance": "-0.10",
        "granted_balance": "0.00",
        "topped_up_balance": "-0.10",
    }],
}


def _mock_response(raw: dict):
    """构造一个 mock httpx.Response。"""
    resp = MagicMock()
    resp.json.return_value = raw
    resp.raise_for_status.return_value = None
    return resp


# ═══════════════════════════════════════════════════════════════
# 余额接口返回标准化
# ═══════════════════════════════════════════════════════════════

class TestGetDeepSeekBalance:
    """get_deepseek_balance 标准化余额接口返回。"""

    def test_normal_balance_parsed(self):
        with patch(
            "app.services.agent.agent_balance_service._client"
        ) as mock_client:
            mock_client.get.return_value = _mock_response(_NORMAL_RAW)
            info = get_deepseek_balance()

        assert info["is_available"] is True
        assert info["total_balance"] == 10.50
        assert info["currency"] == "CNY"
        assert info["granted_balance"] == 5.00
        assert info["topped_up_balance"] == 5.50
        assert isinstance(info["total_balance"], float)

    def test_overdraft_balance_parsed(self):
        with patch(
            "app.services.agent.agent_balance_service._client"
        ) as mock_client:
            mock_client.get.return_value = _mock_response(_OVERDRAFT_RAW)
            info = get_deepseek_balance()

        assert info["is_available"] is False
        assert info["total_balance"] == -0.10
        assert info["currency"] == "CNY"

    def test_empty_balance_infos_no_crash(self):
        """balance_infos 为空时不应崩溃，余额归 0。"""
        with patch(
            "app.services.agent.agent_balance_service._client"
        ) as mock_client:
            mock_client.get.return_value = _mock_response(
                {"is_available": False, "balance_infos": []}
            )
            info = get_deepseek_balance()

        assert info["total_balance"] == 0.0
        assert info["currency"] == "CNY"

    def test_request_uses_bearer_auth(self):
        """验证请求头带 Bearer 鉴权。"""
        with patch(
            "app.services.agent.agent_balance_service._client"
        ) as mock_client:
            mock_client.get.return_value = _mock_response(_NORMAL_RAW)
            get_deepseek_balance()

        args, kwargs = mock_client.get.call_args
        headers = kwargs["headers"]
        assert headers["Authorization"].startswith("Bearer ")

    def test_request_url_correct(self):
        """验证请求 URL 拼接 base_url + /user/balance。"""
        with patch(
            "app.services.agent.agent_balance_service._client"
        ) as mock_client:
            mock_client.get.return_value = _mock_response(_NORMAL_RAW)
            get_deepseek_balance()

        url = mock_client.get.call_args[0][0]
        assert url.endswith("/user/balance")


# ═══════════════════════════════════════════════════════════════
# 降级判断 + 容错
# ═══════════════════════════════════════════════════════════════

class TestCheckBalanceSufficient:
    """check_balance_sufficient 降级判断 + 查询失败容错。"""

    @pytest.mark.asyncio
    async def test_sufficient_balance_above_threshold(self):
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance_async",
            return_value={"total_balance": 10.0},
        ):
            sufficient, balance = await check_balance_sufficient()
        assert sufficient is True
        assert balance == 10.0

    @pytest.mark.asyncio
    async def test_insufficient_balance_below_threshold(self):
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance_async",
            return_value={"total_balance": 0.01},
        ):
            sufficient, balance = await check_balance_sufficient()
        assert sufficient is False
        assert balance == 0.01

    @pytest.mark.asyncio
    async def test_negative_balance_insufficient(self):
        """欠费（负余额）应判为不足。"""
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance_async",
            return_value={"total_balance": -0.10},
        ):
            sufficient, balance = await check_balance_sufficient()
        assert sufficient is False

    @pytest.mark.asyncio
    async def test_query_failure_does_not_block(self):
        """余额查询失败时返回 sufficient=True，不阻断 agent 路线。"""
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance_async",
            side_effect=Exception("network timeout"),
        ):
            sufficient, balance = await check_balance_sufficient()
        assert sufficient is True
        assert balance == -1.0

    @pytest.mark.asyncio
    async def test_threshold_boundary(self):
        """余额恰好等于阈值时应判为充足（>= 阈值）。"""
        with patch(
            "app.services.agent.agent_balance_service.get_deepseek_balance_async",
            return_value={"total_balance": BALANCE_DEGRADE_THRESHOLD},
        ):
            sufficient, _ = await check_balance_sufficient()
        assert sufficient is True
