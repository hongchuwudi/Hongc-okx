"""
创建时间: 2026-07-01
作者: hongchuwudi
描述: 第 4 层语义意图降级测试 — 纯自然语言输出的动作意图识别

覆盖:
- 真实日志样本（继续持多/耐心持有）→ 正确识别
- 否定/条件修饰过滤（不要加仓 / 若下跌再买入）→ 不误判
- 噪音文本保护（适合交易 / signal BUY）→ 仍失败，不被误判为下单
"""

from app.agents.parser import parse_agent_output


def test_intent_hold_patient():
    """真实样本: 空头趋势耐心持有 → HOLD。"""
    raw = "✅ 决策已记录！等待市场验证。空头趋势尚未结束，耐心持有让利润奔跑。"
    res = parse_agent_output(raw)
    assert res.success
    assert res.strategy == "intent"
    assert res.data["signal"] == "HOLD"


def test_intent_buy_add_position():
    """真实样本: 继续持多头并加仓 → BUY（加仓动作优先于持多状态）。"""
    raw = "决策已出！继续持多头并加仓，等待RSI超卖反弹行情到来"
    res = parse_agent_output(raw)
    assert res.success
    assert res.data["signal"] == "BUY"


def test_intent_sell_short():
    """做空动作 → SELL。"""
    res = parse_agent_output("建议做空，趋势破位")
    assert res.success
    assert res.data["signal"] == "SELL"


def test_intent_buy_and_sell_cancel():
    """同时出现加仓和减仓（如对冲描述）→ 互相抵消不触发 BUY/SELL。"""
    res = parse_agent_output("多头加仓同时空头减仓对冲")
    # 同时命中 buy 与 sell → 不提取为 BUY/SELL；无"持有"等 HOLD 短语 → 失败
    assert not res.success or res.data["signal"] == "HOLD"


def test_intent_negation_blocks():
    """否定修饰: 不要加仓，先观望 → 不触发 BUY，观望触发 HOLD。"""
    res = parse_agent_output("当前不要加仓，先观望")
    assert res.success
    assert res.data["signal"] == "HOLD"


def test_intent_conditional_blocks():
    """条件修饰: 若跌破支撑再买入 → 不触发 BUY（动作前含"若"）。"""
    res = parse_agent_output("若跌破支撑再买入")
    assert not res.success


def test_intent_noise_still_fails():
    """噪音文本不含动作短语 → 仍失败（保护现有行为）。"""
    assert not parse_agent_output("今天天气不错，适合交易").success
    assert not parse_agent_output("signal BUY confidence HIGH").success
    assert not parse_agent_output("无效文本").success


def test_intent_confidence_medium():
    """语义降级 confidence 固定 MEDIUM，不自带仓位。"""
    res = parse_agent_output("保持仓位，继续观望")
    assert res.success
    assert res.data["confidence"] == "MEDIUM"
    assert "position_pct" not in res.data or res.data.get("position_pct") in (None, 0, "")