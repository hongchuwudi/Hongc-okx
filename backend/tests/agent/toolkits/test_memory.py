"""
测试: 私有记忆 — remember/recall/check_my_accuracy
"""

import pytest


class TestPrivateMemory:
    def test_remember_and_recall(self):
        from app.agents.toolkits.tools.toolkit_memory_private import create_memory_tools
        tools = create_memory_tools("test_agent")
        remember, recall, accuracy = tools

        r1 = remember.invoke({"key": "last_signal", "value": "BUY"})
        assert "已记住" in r1
        r2 = recall.invoke({"key": "last_signal"})
        assert "BUY" in r2

    def test_recall_empty(self):
        from app.agents.toolkits.tools.toolkit_memory_private import create_memory_tools
        tools = create_memory_tools("test_empty_recall")
        _, recall, _ = tools
        result = recall.invoke({"key": "nonexistent"})
        # 空记忆调用 recall 返回"暂无记忆"
        assert "暂无记忆" in result or "不记得" in result

    def test_accuracy_tracking(self):
        from app.agents.toolkits.tools.toolkit_memory_private import create_memory_tools
        tools = create_memory_tools("acc_test")
        remember, _, accuracy = tools

        remember.invoke({"key": "result_001", "value": "对了 — MACD金叉"})
        remember.invoke({"key": "result_002", "value": "错了 — RSI误判"})
        remember.invoke({"key": "result_003", "value": "对了 — 趋势正确"})

        result = accuracy.invoke({})
        assert "67%" in result or "2/3" in result

    def test_max_entries_enforced(self):
        from app.agents.toolkits.tools.toolkit_memory_private import create_memory_tools, _load_all
        tools = create_memory_tools("max_test2")
        remember, _, _ = tools

        for i in range(25):
            remember.invoke({"key": f"key_{i}", "value": f"val_{i}"})

        store = _load_all("max_test2")
        assert len(store) <= 20


class TestMemoryCrossAgent:
    def test_isolation(self):
        from app.agents.toolkits.tools.toolkit_memory_private import create_memory_tools
        ta = create_memory_tools("agent_a")
        tb = create_memory_tools("agent_b")
        ra, _, _ = ta
        rb, _, _ = tb

        ra.invoke({"key": "secret", "value": "only_a"})

        result_a = ta[1].invoke({"key": "secret"})
        result_b = tb[1].invoke({"key": "secret"})

        assert "only_a" in result_a
        # B 看不到 A 的记忆（空记忆或不存在）
        assert "only_a" not in result_b
