"""数据文本格式化函数

将市场数据、持仓、历史记忆格式化为 Agent 可读的文本块。
"""


def format_market_text(
    price: float,
    indicators: dict,
    trend: dict,
    levels: dict,
    market_state: dict,
) -> str:
    rsi = indicators.get("rsi", 50)
    macd = indicators.get("macd", 0)
    macd_sig = indicators.get("macd_signal", 0)
    bb_pos = indicators.get("bb_position", 0.5)
    sma5 = indicators.get("sma_5", price)
    sma20 = indicators.get("sma_20", price)
    sma50 = indicators.get("sma_50", price)
    vol_ratio = indicators.get("volume_ratio", 1.0)

    rsi_label = "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性")

    return f"""
【行情数据】
BTC 当前价格: ${price:,.2f}
市场状态: {market_state.get('state', 'N/A')} (波动率 ATR: {market_state.get('atr_pct', 0):.2f}%)

【均线】
SMA5: {sma5:.0f} | SMA20: {sma20:.0f} | SMA50: {sma50:.0f}
价格 vs SMA20: {((price - sma20) / sma20 * 100):+.2f}% | vs SMA50: {((price - sma50) / sma50 * 100):+.2f}%

【趋势】{trend.get('overall', 'N/A')} (短: {trend.get('short_term', 'N/A')}, 中: {trend.get('medium_term', 'N/A')})

【动量】RSI(14): {rsi:.1f} ({rsi_label}) | MACD: {macd:.1f} vs {macd_sig:.1f} ({trend.get('macd', 'N/A')})

【布林带】位置: {bb_pos:.1%} | 上轨: {indicators.get('bb_upper', 0):.0f} | 下轨: {indicators.get('bb_lower', 0):.0f}

【成交量】量比: {vol_ratio:.2f} (1=正常)

【支撑阻力】
静态阻力: {levels.get('static_resistance', 0):.0f} (距 {levels.get('price_vs_resistance', 0):.1f}%)
静态支撑: {levels.get('static_support', 0):.0f} (距 {levels.get('price_vs_support', 0):.1f}%)
动态上轨: {levels.get('dynamic_resistance', 0):.0f} | 下轨: {levels.get('dynamic_support', 0):.0f}
"""


def format_position_text(position: dict | None) -> str:
    if not position or not position.get("side"):
        return "当前持仓: 无（空仓）"

    side = "多头" if position["side"] == "long" else "空头"
    return (
        f"当前持仓: {side} {position.get('size', 0)} 张 | "
        f"入场价: ${position.get('entry_price', 0):.2f} | "
        f"浮动盈亏: ${position.get('unrealized_pnl', 0):.2f} | "
        f"杠杆: {position.get('leverage', 1)}x"
    )


def format_memory_text() -> str:
    from app.memory import memory_store

    stats = memory_store.get_stats()
    recent = memory_store.get_recent(8)

    lines = ["【历史绩效】"]
    lines.append(
        f"总决策: {stats['total']} | 已结算: {stats.get('closed', 0)} | "
        f"胜率: {stats['win_rate']}% | 平均盈亏: {stats['avg_pnl']:.4f} USDT"
    )
    lines.append(f"近期趋势: {stats['recent_trend']}")

    if recent:
        lines.append("--- 最近决策 ---")
        for m in recent:
            outcome = ""
            if m.get("outcome_pnl") is not None:
                sign = "+" if (m["outcome_pnl"] or 0) >= 0 else ""
                outcome = f" => {sign}{m['outcome_pnl']:.2f} USDT {'(赢)' if m.get('is_win') else '(亏)'}"
            lines.append(
                f"{m.get('timestamp', '')} | {m.get('signal', ''):4s} @ "
                f"${m.get('price', 0):,.0f} | {str(m.get('reason', ''))[:60]}{outcome}"
            )

    return "\n".join(lines)
