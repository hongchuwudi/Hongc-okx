"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_agent_pipeline.py Agent 流水线集成测试
描述: 3 种 Agent 模式的完整执行链路测试，使用 data/ 真实 K 线数据

每种模式只调用一次 LLM（class-scoped fixture），所有断言复用同一结果。
总耗时约 2-3 分钟（5-agent ~90s + 3-agent ~40s + solo ~20s）。

覆盖:
- 5 Agent Swarm: scheduler → analyst ∥ reviewer → risk → trader
- 3 Agent Swarm: super_analyst → risk → trader
- 1 Agent Solo: 预计算指标 → solo → 决策

验证:
- analyze() 返回 dict 结构完整
- signal/confidence/sl/tp/position_pct 字段有效
- agent_reports 包含正确的 Agent 名称
- source_count 匹配模式
- 中间输出（risk 风控、trader 解析等）非空
"""
import asyncio

import pandas as pd
import pytest

# 测试用的 DOGE 3m K 线数据路径
_KLINE_PATH = "data/kline/demo/doge/doge_3m_2026-06-18_073000_2026-06-22_112700.csv"

_VALID_SIGNALS = {"BUY", "SELL", "HOLD"}
_VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}


# ═══════════════════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════════════════

def _load_kline(path: str = _KLINE_PATH, n_rows: int = 200) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df.tail(n_rows).copy()


def _get_latest_price(df: pd.DataFrame) -> float:
    return float(df["close"].iloc[-1])


# ═══════════════════════════════════════════════════════════════
# 公共断言
# ═══════════════════════════════════════════════════════════════

def assert_valid_decision(result: dict, source_count: int,
                          expected_agent_names: list[str]):
    """验证 agent analyze() 返回的决策 dict 每个字段。"""
    assert isinstance(result, dict), f"返回值应为 dict，实际 {type(result)}"
    for key in ("signal", "confidence", "reason", "stop_loss",
                "take_profit", "position_pct", "source_count", "agent_reports"):
        assert key in result, f"缺少 key: {key}"

    # signal
    assert result["signal"] in _VALID_SIGNALS, f"signal={result['signal']}"
    # confidence
    assert result["confidence"] in _VALID_CONFIDENCE, f"confidence={result['confidence']}"
    # reason
    assert isinstance(result["reason"], str) and len(result["reason"]) > 0
    # sl/tp
    sl, tp = float(result["stop_loss"]), float(result["take_profit"])
    assert sl > 0 and tp > 0
    if result["signal"] == "BUY":
        assert sl < tp, f"BUY: sl({sl}) >= tp({tp})"
    elif result["signal"] == "SELL":
        assert sl > tp, f"SELL: sl({sl}) <= tp({tp})"
    # position_pct
    pct = float(result["position_pct"])
    assert 0 <= pct <= 100, f"position_pct={pct}"
    if result["signal"] in ("BUY", "SELL"):
        assert pct > 0, f"非HOLD pct={pct} 应>0"
    # source_count
    assert result["source_count"] == source_count, f"source_count={result['source_count']}"
    # agent_reports
    reports = result["agent_reports"]
    assert isinstance(reports, dict)
    for name in expected_agent_names:
        assert name in reports, f"agent_reports 缺少 {name}"
        assert reports[name] and len(str(reports[name])) > 20, (
            f"agent_reports[{name}] 内容过短"
        )


# ═══════════════════════════════════════════════════════════════
# class-scoped fixtures: 每种模式只跑一次 LLM
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def five_agent_result():
    """5 Agent Swarm 运行一次，全模块共享结果。"""
    from app.agents.coordinators.coordinator_5 import AgentCoordinator

    df = _load_kline()
    price = _get_latest_price(df)
    coordinator = AgentCoordinator()
    return asyncio.run(coordinator.analyze(df, price, 10000.0, position=None))


@pytest.fixture(scope="module")
def three_agent_result():
    """3 Agent Swarm 运行一次，全模块共享结果。"""
    from app.agents.coordinators.coordinator_3 import AgentCoordinator3

    df = _load_kline()
    price = _get_latest_price(df)
    coordinator = AgentCoordinator3()
    return asyncio.run(coordinator.analyze(df, price, 10000.0, position=None))


@pytest.fixture(scope="module")
def solo_agent_result():
    """1 Agent Solo 运行一次，全模块共享结果。"""
    from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo

    df = _load_kline()
    price = _get_latest_price(df)
    coordinator = AgentCoordinatorSolo()
    return asyncio.run(coordinator.analyze(df, price, 10000.0, position=None))


# ═══════════════════════════════════════════════════════════════
# 5 Agent Swarm
# ═══════════════════════════════════════════════════════════════

class TestFiveAgentPipeline:
    """5 Agent Swarm: scheduler → analyst ∥ reviewer → risk → trader"""

    def test_structure_valid(self, five_agent_result):
        """顶层结构 + 字段有效性。"""
        assert_valid_decision(five_agent_result, 5, [
            "scheduler", "analyst", "reviewer", "risk", "trader",
        ])

    def test_scheduler_has_focus(self, five_agent_result):
        """调度师应输出足够的分析内容。"""
        r = str(five_agent_result["agent_reports"]["scheduler"])
        assert len(r) > 30, f"调度师报告过短: {r[:100]}"

    def test_risk_go_no_go_meaningful(self, five_agent_result):
        """风控报告应包含风险评估关键词。"""
        r = str(five_agent_result["agent_reports"]["risk"]).lower()
        keywords = ["risk", "风险", "go", "no_go", "position", "仓位", "drawdown", "回撤"]
        assert any(k in r for k in keywords), f"风控报告缺关键词: {r[:200]}"

    def test_trader_parseable(self, five_agent_result):
        """Trader 输出应包含 JSON 或结构化信号。"""
        r = str(five_agent_result["agent_reports"]["trader"]).lower()
        assert "{" in r or "signal" in r, f"Trader 输出应可解析: {r[:200]}"


# ═══════════════════════════════════════════════════════════════
# 3 Agent Swarm
# ═══════════════════════════════════════════════════════════════

class TestThreeAgentPipeline:
    """3 Agent Swarm: super_analyst → risk → trader"""

    def test_structure_valid(self, three_agent_result):
        assert_valid_decision(three_agent_result, 3, [
            "super_analyst", "risk", "trader",
        ])

    def test_source_count_is_3(self, three_agent_result):
        assert three_agent_result["source_count"] == 3
        assert len(three_agent_result["agent_reports"]) == 3

    def test_super_analyst_report_rich(self, three_agent_result):
        r = str(three_agent_result["agent_reports"]["super_analyst"])
        assert len(r) > 50, f"超分报告过短: {r[:100]}"


# ═══════════════════════════════════════════════════════════════
# 1 Agent Solo
# ═══════════════════════════════════════════════════════════════

class TestSoloAgentPipeline:
    """1 Agent 急速模式: 预计算指标 → solo → 决策"""

    def test_structure_valid(self, solo_agent_result):
        assert_valid_decision(solo_agent_result, 1, ["solo"])

    def test_source_count_is_1(self, solo_agent_result):
        assert solo_agent_result["source_count"] == 1
        assert list(solo_agent_result["agent_reports"].keys()) == ["solo"]

    def test_report_rich(self, solo_agent_result):
        r = str(solo_agent_result["agent_reports"]["solo"])
        assert len(r) > 50, f"Solo 报告过短: {r[:100]}"


# ═══════════════════════════════════════════════════════════════
# 跨模式一致性
# ═══════════════════════════════════════════════════════════════

class TestCrossModeConsistency:
    """3 种模式输出结构一致性"""

    def test_all_same_top_level_keys(self, five_agent_result,
                                     three_agent_result, solo_agent_result):
        expected = {"signal", "confidence", "reason", "stop_loss",
                    "take_profit", "position_pct", "source_count", "agent_reports"}
        assert set(five_agent_result.keys()) == expected
        assert set(three_agent_result.keys()) == expected
        assert set(solo_agent_result.keys()) == expected

    def test_all_return_valid_signal(self, five_agent_result,
                                      three_agent_result, solo_agent_result):
        for name, r in [("5-agent", five_agent_result),
                        ("3-agent", three_agent_result),
                        ("solo", solo_agent_result)]:
            assert r["signal"] in _VALID_SIGNALS, f"{name}: {r['signal']}"
            assert r["confidence"] in _VALID_CONFIDENCE, f"{name}: {r['confidence']}"
            print(f"\n[{name}] {r['signal']} ({r['confidence']}) "
                  f"SL={r['stop_loss']:.6f} TP={r['take_profit']:.6f} "
                  f"pct={r['position_pct']}%")
