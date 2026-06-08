"""
Created: 2026-06-14
Author: hongchuwudi
Description: DeepSeek 策略辅助函数 — 信号验证、止盈止损计算、prompt 构建

Contains:
- Function: safe_json_parse — 安全解析 AI 输出的 JSON
- Function: fallback_signal — AI 失败时的保守默认信号
- Function: calc_dynamic_tp_sl — 根据市场状态动态计算止盈止损
- Function: validate_signal — 用技术指标修正 AI 信号
- Function: generate_technical_analysis_text — 构建技术分析文本供 AI 阅读
"""

import pandas as pd
from app.core.logger import get_logger
from app.services.agent.agent_coordinator_service import parse_agent_output

logger = get_logger()


def safe_json_parse(text: str):
    return parse_agent_output(text)


def fallback_signal(price: float) -> dict:
    return {
        "signal": "HOLD",
        "reason": "因技术分析暂时不可用，采取保守策略",
        "stop_loss": price * 0.98,
        "take_profit": price * 1.02,
        "confidence": "LOW",
        "is_fallback": True,
    }


def calc_dynamic_tp_sl(signal: str, price: float, market_state: dict, position: dict = None) -> dict:
    atr_pct = market_state.get("atr_pct", 2.0)
    state = market_state.get("state", "")
    if state.startswith("高波动"):
        sl_pct, tp_pct = 0.025, 0.06
    elif state.startswith("低波动"):
        sl_pct, tp_pct = 0.015, 0.03
    else:
        sl_pct, tp_pct = 0.02, 0.05

    if signal == "BUY":
        stop_loss = price * (1 - sl_pct)
        take_profit = price * (1 + tp_pct)
    elif signal == "SELL":
        stop_loss = price * (1 + sl_pct)
        take_profit = price * (1 - tp_pct)
    else:
        stop_loss = price * 0.98
        take_profit = price * 1.02

    if position and position.get("unrealized_pnl", 0) > 0:
        ep = position.get("entry_price", price)
        sz = position.get("size", 0)
        if ep > 0 and sz > 0:
            profit_pct = position["unrealized_pnl"] / (ep * sz * 0.01)
            if profit_pct > 0.05:
                if position["side"] == "long":
                    stop_loss = max(stop_loss, ep * 1.01)
                else:
                    stop_loss = min(stop_loss, ep * 0.99)
                logger.info(f"盈利{profit_pct:.1%}，移动止损到保本+1%: {stop_loss:.2f}")
    return {
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "sl_pct": sl_pct,
        "tp_pct": tp_pct,
    }


def validate_signal(ai_signal: dict, price_data: dict, tech_data: dict) -> dict:
    signal = ai_signal.get("signal", "HOLD")
    tech = tech_data
    rsi = tech.get("rsi", 50)

    if rsi > 80 and signal == "BUY":
        logger.warning("RSI超买(>80)，降低BUY信号信心")
        ai_signal["confidence"] = "LOW"
        ai_signal["reason"] += " [RSI超买警告]"
    if rsi < 20 and signal == "SELL":
        logger.warning("RSI超卖(<20)，降低SELL信号信心")
        ai_signal["confidence"] = "LOW"
        ai_signal["reason"] += " [RSI超卖警告]"

    trend = price_data.get("trend_analysis", {}).get("overall", "震荡整理")
    conf = ai_signal.get("confidence", "MEDIUM")
    if trend == "强势上涨" and signal == "SELL" and conf != "HIGH":
        ai_signal["signal"] = "HOLD"
        ai_signal["reason"] = "趋势与信号冲突，保持观望"
        logger.info("信号已修正为HOLD")
    if trend == "强势下跌" and signal == "BUY" and conf != "HIGH":
        ai_signal["signal"] = "HOLD"
        ai_signal["reason"] = "趋势与信号冲突，保持观望"
        logger.info("信号已修正为HOLD")

    macd = tech.get("macd", 0)
    macd_sig = tech.get("macd_signal", 0)
    if macd > macd_sig and signal == "SELL":
        logger.warning("MACD多头但信号SELL，降低信心")
        if ai_signal.get("confidence") == "HIGH":
            ai_signal["confidence"] = "MEDIUM"
    if macd < macd_sig and signal == "BUY":
        logger.warning("MACD空头但信号BUY，降低信心")
        if ai_signal.get("confidence") == "HIGH":
            ai_signal["confidence"] = "MEDIUM"

    price = price_data["price"]
    if signal == "BUY":
        if ai_signal.get("stop_loss", 0) >= price:
            ai_signal["stop_loss"] = price * 0.98
        if ai_signal.get("take_profit", 0) <= price:
            ai_signal["take_profit"] = price * 1.03
    elif signal == "SELL":
        if ai_signal.get("stop_loss", 0) <= price:
            ai_signal["stop_loss"] = price * 1.02
        if ai_signal.get("take_profit", 0) >= price:
            ai_signal["take_profit"] = price * 0.97
    return ai_signal


def generate_technical_analysis_text(price_data: dict) -> str:
    if "technical_data" not in price_data:
        return "技术指标数据不可用"
    tech = price_data["technical_data"]
    trend = price_data.get("trend_analysis", {})
    levels = price_data.get("levels_analysis", {})

    def sf(v, d=0):
        return float(v) if v and pd.notna(v) else d

    return f"""
【技术指标分析】
📈 移动平均线:
- 5周期: {sf(tech["sma_5"]):.2f} | 价格相对: {(price_data["price"] - sf(tech["sma_5"])) / sf(tech["sma_5"]) * 100:+.2f}%
- 20周期: {sf(tech["sma_20"]):.2f} | 价格相对: {(price_data["price"] - sf(tech["sma_20"])) / sf(tech["sma_20"]) * 100:+.2f}%
- 50周期: {sf(tech["sma_50"]):.2f} | 价格相对: {(price_data["price"] - sf(tech["sma_50"])) / sf(tech["sma_50"]) * 100:+.2f}%

🎯 趋势分析:
- 短期趋势: {trend.get("short_term", "N/A")}
- 中期趋势: {trend.get("medium_term", "N/A")}
- 整体趋势: {trend.get("overall", "N/A")}
- MACD方向: {trend.get("macd", "N/A")}

📊 动量指标:
- RSI: {sf(tech["rsi"]):.2f} ({"超买" if sf(tech["rsi"]) > 70 else "超卖" if sf(tech["rsi"]) < 30 else "中性"})
- MACD: {sf(tech["macd"]):.4f}
- 信号线: {sf(tech["macd_signal"]):.4f}

🎚️ 布林带位置: {sf(tech["bb_position"]):.2%} ({"上部" if sf(tech["bb_position"]) > 0.7 else "下部" if sf(tech["bb_position"]) < 0.3 else "中部"})

💰 关键水平:
- 静态阻力: {sf(levels.get("static_resistance", 0)):.2f}
- 静态支撑: {sf(levels.get("static_support", 0)):.2f}
"""
