"""
DeepSeek AI 策略 — 从 deepseekok2.py 提取的信号生成逻辑
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import requests

from base_strategy import BaseStrategy
from logger import get_logger

logger = get_logger()


class DeepSeekStrategy(BaseStrategy):
    """DeepSeek AI 驱动的交易策略"""

    def __init__(self, config: dict, openai_client, exchange=None):
        self.config = config
        self.client = openai_client
        self.exchange = exchange
        self.signal_history: List[Dict] = []
        self._sentiment_api_key = "7ad48a56-8730-4238-a714-eebc30834e3e"

    @property
    def name(self) -> str:
        return "DeepSeekStrategy"

    # ── public API ──────────────────────────────────────────

    def generate_signal(
        self,
        df: pd.DataFrame,
        current_position: Optional[Dict] = None,
        **kwargs,
    ) -> Dict:
        """主入口: 对给定的 OHLCV DataFrame 生成交易信号"""
        return self._analyze_with_retry(df, current_position)

    def get_current_position(self) -> Optional[Dict]:
        """获取当前持仓（需要 exchange 实例）"""
        if self.exchange is None:
            return None
        try:
            symbol = self.config["symbol"]
            positions = self.exchange.fetch_positions([symbol])
            for pos in positions:
                if pos["symbol"] == symbol and float(pos.get("contracts", 0)) > 0:
                    return {
                        "side": pos["side"],
                        "size": float(pos["contracts"]),
                        "entry_price": float(pos.get("entryPrice", 0)),
                        "unrealized_pnl": float(pos.get("unrealizedPnl", 0)),
                        "leverage": float(pos.get("leverage", self.config["leverage"])),
                        "symbol": pos["symbol"],
                    }
            return None
        except Exception as e:
            logger.info(f"获取持仓失败: {e}")
            return None

    # ── internal helpers ────────────────────────────────────

    def _build_price_data(self, df: pd.DataFrame) -> dict:
        """从 OHLCV DataFrame 构建与原始代码兼容的 price_data 字典"""
        df = self._calc_indicators(df)
        last = df.iloc[-1]
        prev = df.iloc[-2]

        trend = self._get_market_trend(df)
        levels = self._get_support_resistance_levels(df)

        return {
            "price": last["close"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "high": last["high"],
            "low": last["low"],
            "volume": last["volume"],
            "timeframe": self.config["timeframe"],
            "price_change": ((last["close"] - prev["close"]) / prev["close"]) * 100,
            "kline_data": df[["timestamp", "open", "high", "low", "close", "volume"]]
            .tail(10)
            .to_dict("records"),
            "technical_data": {
                "sma_5": last.get("sma_5", 0),
                "sma_20": last.get("sma_20", 0),
                "sma_50": last.get("sma_50", 0),
                "rsi": last.get("rsi", 0),
                "macd": last.get("macd", 0),
                "macd_signal": last.get("macd_signal", 0),
                "macd_histogram": last.get("macd_histogram", 0),
                "bb_upper": last.get("bb_upper", 0),
                "bb_lower": last.get("bb_lower", 0),
                "bb_position": last.get("bb_position", 0),
                "volume_ratio": last.get("volume_ratio", 0),
            },
            "trend_analysis": trend,
            "levels_analysis": levels,
            "full_data": df,
        }

    def _calc_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            df["sma_5"] = df["close"].rolling(window=5, min_periods=1).mean()
            df["sma_20"] = df["close"].rolling(window=20, min_periods=1).mean()
            df["sma_50"] = df["close"].rolling(window=50, min_periods=1).mean()
            df["ema_12"] = df["close"].ewm(span=12).mean()
            df["ema_26"] = df["close"].ewm(span=26).mean()
            df["macd"] = df["ema_12"] - df["ema_26"]
            df["macd_signal"] = df["macd"].ewm(span=9).mean()
            df["macd_histogram"] = df["macd"] - df["macd_signal"]
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))
            df["bb_middle"] = df["close"].rolling(20).mean()
            bb_std = df["close"].rolling(20).std()
            df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
            df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
            df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
            df["volume_ma"] = df["volume"].rolling(20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_ma"]
            df = df.bfill().ffill()
            return df
        except Exception as e:
            logger.info(f"技术指标计算失败: {e}")
            return df

    def _get_support_resistance_levels(self, df, lookback=20):
        try:
            recent_high = df["high"].tail(lookback).max()
            recent_low = df["low"].tail(lookback).min()
            price = df["close"].iloc[-1]
            return {
                "static_resistance": recent_high,
                "static_support": recent_low,
                "dynamic_resistance": df["bb_upper"].iloc[-1],
                "dynamic_support": df["bb_lower"].iloc[-1],
                "price_vs_resistance": ((recent_high - price) / price) * 100,
                "price_vs_support": ((price - recent_low) / recent_low) * 100,
            }
        except Exception as e:
            logger.info(f"支撑阻力计算失败: {e}")
            return {}

    def _get_market_trend(self, df):
        try:
            price = df["close"].iloc[-1]
            trend_short = "上涨" if price > df["sma_20"].iloc[-1] else "下跌"
            trend_medium = "上涨" if price > df["sma_50"].iloc[-1] else "下跌"
            macd_trend = "bullish" if df["macd"].iloc[-1] > df["macd_signal"].iloc[-1] else "bearish"
            if trend_short == "上涨" and trend_medium == "上涨":
                overall = "强势上涨"
            elif trend_short == "下跌" and trend_medium == "下跌":
                overall = "强势下跌"
            else:
                overall = "震荡整理"
            return {
                "short_term": trend_short,
                "medium_term": trend_medium,
                "macd": macd_trend,
                "overall": overall,
                "rsi_level": df["rsi"].iloc[-1],
            }
        except Exception as e:
            logger.info(f"趋势分析失败: {e}")
            return {}

    def _get_sentiment(self):
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=4)
            body = {
                "apiKey": self._sentiment_api_key,
                "endpoints": ["CO-A-02-01", "CO-A-02-02"],
                "startTime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "endTime": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "timeType": "15m",
                "token": ["BTC"],
            }
            headers = {"Content-Type": "application/json", "X-API-KEY": self._sentiment_api_key}
            resp = requests.post(
                "https://service.cryptoracle.network/openapi/v2/endpoint",
                json=body,
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200 and data.get("data"):
                    for period in data["data"][0]["timePeriods"]:
                        sentiment = {}
                        for item in period.get("data", []):
                            ep = item.get("endpoint")
                            val = item.get("value", "").strip()
                            if val and ep in ("CO-A-02-01", "CO-A-02-02"):
                                try:
                                    sentiment[ep] = float(val)
                                except (ValueError, TypeError):
                                    continue
                        if "CO-A-02-01" in sentiment and "CO-A-02-02" in sentiment:
                            net = sentiment["CO-A-02-01"] - sentiment["CO-A-02-02"]
                            return {
                                "positive_ratio": sentiment["CO-A-02-01"],
                                "negative_ratio": sentiment["CO-A-02-02"],
                                "net_sentiment": net,
                                "data_time": period["startTime"],
                            }
                    logger.error("所有时间段数据都为空")
            return None
        except Exception as e:
            logger.info(f"情绪指标获取失败: {e}")
            return None

    def _generate_technical_analysis_text(self, price_data) -> str:
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

    def _identify_market_state(self, price_data, tech_data) -> dict:
        try:
            df = price_data["full_data"]
            atr = (df["high"] - df["low"]).rolling(14).mean()
            atr_pct = (atr.iloc[-1] / price_data["price"]) * 100
            sma_5 = tech_data.get("sma_5", 0)
            sma_20 = tech_data.get("sma_20", 0)
            sma_50 = tech_data.get("sma_50", 0)
            if sma_5 > sma_20 > sma_50:
                ts, conf = "强上涨", 0.9
            elif sma_5 < sma_20 < sma_50:
                ts, conf = "强下跌", 0.9
            elif abs(sma_5 - sma_20) / sma_20 < 0.005:
                ts, conf = "震荡", 0.7
            else:
                ts, conf = "弱趋势", 0.5
            if atr_pct > 3:
                state = "高波动" + ts
            elif atr_pct < 1:
                state = "低波动震荡"
            else:
                state = ts
            return {"state": state, "confidence": conf, "atr_pct": atr_pct, "trend_strength": ts}
        except Exception as e:
            logger.info(f"市场状态识别失败: {e}")
            return {"state": "未知", "confidence": 0.5, "atr_pct": 2.0, "trend_strength": "未知"}

    def _calc_dynamic_tp_sl(self, signal, price, market_state, position=None):
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
                    logger.info(f"📈 盈利{profit_pct:.1%}，移动止损到保本+1%: {stop_loss:.2f}")

        return {
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "sl_pct": sl_pct,
            "tp_pct": tp_pct,
        }

    def _validate_signal(self, ai_signal, price_data, tech_data):
        signal = ai_signal.get("signal", "HOLD")
        tech = tech_data
        rsi = tech.get("rsi", 50)

        if rsi > 80 and signal == "BUY":
            logger.warning("⚠️ RSI超买(>80)，降低BUY信号信心")
            ai_signal["confidence"] = "LOW"
            ai_signal["reason"] += " [RSI超买警告]"
        if rsi < 20 and signal == "SELL":
            logger.warning("⚠️ RSI超卖(<20)，降低SELL信号信心")
            ai_signal["confidence"] = "LOW"
            ai_signal["reason"] += " [RSI超卖警告]"

        trend = price_data.get("trend_analysis", {}).get("overall", "震荡整理")
        conf = ai_signal.get("confidence", "MEDIUM")
        if trend == "强势上涨" and signal == "SELL" and conf != "HIGH":
            ai_signal["signal"] = "HOLD"
            ai_signal["reason"] = "趋势与信号冲突，保持观望"
            logger.info("🔄 信号已修正为HOLD")
        if trend == "强势下跌" and signal == "BUY" and conf != "HIGH":
            ai_signal["signal"] = "HOLD"
            ai_signal["reason"] = "趋势与信号冲突，保持观望"
            logger.info("🔄 信号已修正为HOLD")

        macd = tech.get("macd", 0)
        macd_sig = tech.get("macd_signal", 0)
        if macd > macd_sig and signal == "SELL":
            logger.warning("⚠️ MACD多头但信号SELL，降低信心")
            if ai_signal.get("confidence") == "HIGH":
                ai_signal["confidence"] = "MEDIUM"
        if macd < macd_sig and signal == "BUY":
            logger.warning("⚠️ MACD空头但信号BUY，降低信心")
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

    def _safe_json_parse(self, text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                text = text.replace("'", '"')
                text = re.sub(r"(\w+):", r'"\1":', text)
                text = re.sub(r",\s*}", "}", text)
                text = re.sub(r",\s*]", "]", text)
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.info(f"JSON解析失败: {text}")
                logger.info(f"错误详情: {e}")
                return None

    def _fallback_signal(self, price) -> Dict:
        return {
            "signal": "HOLD",
            "reason": "因技术分析暂时不可用，采取保守策略",
            "stop_loss": price * 0.98,
            "take_profit": price * 1.02,
            "confidence": "LOW",
            "is_fallback": True,
        }

    def _analyze_with_retry(self, df: pd.DataFrame, position=None, max_retries=2) -> Dict:
        for attempt in range(max_retries):
            try:
                result = self._analyze(df, position)
                if result and not result.get("is_fallback"):
                    return result
                logger.warning(f"第{attempt + 1}次尝试失败，进行重试...")
            except Exception as e:
                logger.warning(f"第{attempt + 1}次尝试异常: {e}")
                if attempt == max_retries - 1:
                    price = float(df["close"].iloc[-1])
                    return self._fallback_signal(price)
        price = float(df["close"].iloc[-1])
        return self._fallback_signal(price)

    def _analyze(self, df: pd.DataFrame, position=None) -> Dict:
        price_data = self._build_price_data(df)
        tech_analysis = self._generate_technical_analysis_text(price_data)

        kline_text = f"【最近5根{self.config['timeframe']}K线数据】\n"
        for i, k in enumerate(price_data["kline_data"][-5:]):
            trend = "阳线" if k["close"] > k["open"] else "阴线"
            chg = ((k["close"] - k["open"]) / k["open"]) * 100
            kline_text += f"K线{i + 1}: {trend} 开盘:{k['open']:.2f} 收盘:{k['close']:.2f} 涨跌:{chg:+.2f}%\n"

        signal_text = ""
        if self.signal_history:
            last = self.signal_history[-1]
            signal_text = f"\n【上次信号】{last.get('signal', 'N/A')} (信心: {last.get('confidence', 'N/A')})"

        sent = self._get_sentiment()
        if sent:
            sign = "+" if sent["net_sentiment"] >= 0 else ""
            sentiment_text = f"【市场情绪】乐观{sent['positive_ratio']:.1%} 悲观{sent['negative_ratio']:.1%} 净值{sign}{sent['net_sentiment']:.3f}"
        else:
            sentiment_text = "【市场情绪】数据暂不可用"

        cur_pos = position or self.get_current_position()
        if cur_pos:
            pos_text = f"{cur_pos['side']}仓, 数量: {cur_pos['size']}, 盈亏: {cur_pos['unrealized_pnl']:.2f}USDT"
        else:
            pos_text = "无持仓"

        tech_data = price_data.get("technical_data", {})
        market_state = self._identify_market_state(price_data, tech_data)
        suggested = self._calc_dynamic_tp_sl("BUY", price_data["price"], market_state, cur_pos)
        tp_sl_hint = f"建议止损±{suggested['sl_pct'] * 100:.1f}%, 止盈±{suggested['tp_pct'] * 100:.1f}%"

        prompt = f"""
你是专业的BTC交易分析师。{self.config['timeframe']}周期分析：

【核心数据】
价格: ${price_data['price']:,.2f} ({price_data['price_change']:+.2f}%)
市场状态: {market_state['state']} (波动率: {market_state['atr_pct']:.2f}%)
趋势: {price_data['trend_analysis'].get('overall', 'N/A')}
RSI: {price_data['technical_data'].get('rsi', 0):.1f} | MACD: {price_data['trend_analysis'].get('macd', 'N/A')}
持仓: {pos_text}
{signal_text}

{kline_text}

{tech_analysis}

{sentiment_text}

【决策规则】
1. 强趋势市场(均线多头/空头排列) → 跟随趋势 BUY/SELL
2. 震荡市场(均线纠缠) → 等待突破 HOLD
3. 反转信号 → 需2+指标确认
4. RSI仅辅助，不作主要依据
5. BTC偏多头，上涨趋势可积极

【止盈止损】
{tp_sl_hint}
- 持仓盈利>5% → 移动止损到保本+1%
- 持仓亏损>3% → 考虑止损

【输出格式】
严格JSON格式：
{{
    "signal": "BUY|SELL|HOLD",
    "reason": "核心理由(30字内)",
    "stop_loss": 具体价格数字,
    "take_profit": 具体价格数字,
    "confidence": "HIGH|MEDIUM|LOW"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"您是专业交易员，专注{self.config['timeframe']}周期趋势分析。严格输出JSON格式，不要添加任何解释文字。",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
                temperature=0.1,
            )

            result = response.choices[0].message.content
            logger.info(f"🤖 AI原始回复: {result[:200]}...")

            start_idx = result.find("{")
            end_idx = result.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                signal_data = self._safe_json_parse(result[start_idx:end_idx])
                if signal_data is None:
                    signal_data = self._fallback_signal(price_data["price"])
            else:
                signal_data = self._fallback_signal(price_data["price"])

            required = ["signal", "reason", "stop_loss", "take_profit", "confidence"]
            if not all(f in signal_data for f in required):
                signal_data = self._fallback_signal(price_data["price"])

            logger.info(f"📊 AI原始信号: {signal_data['signal']} (信心: {signal_data['confidence']})")
            signal_data = self._validate_signal(signal_data, price_data, tech_data)
            logger.info(f"✅ 验证后信号: {signal_data['signal']} (信心: {signal_data['confidence']})")

            # 动态止盈止损覆盖
            if signal_data["signal"] != "HOLD":
                dynamic = self._calc_dynamic_tp_sl(
                    signal_data["signal"], price_data["price"], market_state, cur_pos
                )
                ai_sl = signal_data.get("stop_loss", 0)
                ai_tp = signal_data.get("take_profit", 0)
                cp = price_data["price"]
                if signal_data["signal"] == "BUY":
                    sl_ok = ai_sl < cp and ai_sl > cp * 0.95
                    tp_ok = ai_tp > cp and ai_tp < cp * 1.10
                else:
                    sl_ok = ai_sl > cp and ai_sl < cp * 1.05
                    tp_ok = ai_tp < cp and ai_tp > cp * 0.90
                if not sl_ok or not tp_ok:
                    logger.warning(
                        f"⚠️ AI止盈止损不合理，使用动态计算: SL={dynamic['stop_loss']}, TP={dynamic['take_profit']}"
                    )
                    signal_data["stop_loss"] = dynamic["stop_loss"]
                    signal_data["take_profit"] = dynamic["take_profit"]

            signal_data["timestamp"] = price_data["timestamp"]
            self.signal_history.append(signal_data)
            if len(self.signal_history) > 30:
                self.signal_history.pop(0)

            # 信号统计
            same = sum(1 for s in self.signal_history if s.get("signal") == signal_data["signal"])
            logger.info(f"信号统计: {signal_data['signal']} (最近{len(self.signal_history)}次中出现{same}次)")

            if len(self.signal_history) >= 3:
                last3 = [s["signal"] for s in self.signal_history[-3:]]
                if len(set(last3)) == 1:
                    logger.warning(f"⚠️ 注意：连续3次{signal_data['signal']}信号")

            return signal_data

        except Exception as e:
            logger.info(f"DeepSeek分析失败: {e}")
            return self._fallback_signal(price_data["price"])
