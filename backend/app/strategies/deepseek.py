"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: deepseek.py 中文名
描述: DeepSeek AI 策略 — 基于大模型和行情指标生成交易信号

包含:
- 类: DeepSeekStrategy — DeepSeek AI 策略实现，通过 LLM 分析市场数据生成信号
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import requests

from app.config import config as app_config
from app.strategies.base import BaseStrategy
from app.strategies._strategy_helpers import (
    safe_json_parse, fallback_signal, calc_dynamic_tp_sl,
    validate_signal, generate_technical_analysis_text,
)
from app.strategies._strategy_indicator import (
    calc_indicators, get_support_resistance_levels,
    get_market_trend, identify_market_state,
)
from app.core.logger import get_logger

logger = get_logger()


# DeepSeek AI 策略 — 调用大模型分析行情数据，结合技术指标生成交易信号
class DeepSeekStrategy(BaseStrategy):

    def __init__(self, config: dict, openai_client, exchange=None):
        # 策略配置（含交易对、时间周期等）
        self.config = config
        # OpenAI 兼容客户端（用于调用 DeepSeek API）
        self.client = openai_client
        # 交易所客户端（用于获取实时持仓）
        self.exchange = exchange
        # 历史信号记录（用于趋势判断）
        self.signal_history: List[Dict] = []
        # Cryptoracle 情绪指标 API Key
        self._sentiment_api_key = app_config.ai.cryptoracle_api_key
        # 连续失败计数 — 超过阈值跳过重试避免日志刷屏
        self._consecutive_failures = 0
        # 回测模式：每 N 根 K 线调一次 API，其余复用上次信号
        self._backtest = config.get("backtest", False)
        self._bt_interval = config.get("backtest_interval", 20)
        self._bt_bar = 0
        self._bt_last_signal: Dict = {}

    @property
    def name(self) -> str:
        return "DeepSeekStrategy"

    # 生成交易信号（带自动重试）
    def generate_signal(
        self,
        df: pd.DataFrame,
        current_position: Optional[Dict] = None,
        **kwargs,
    ) -> Dict:
        # 回测模式：每 N 根 K 线调一次 API，其余复用上次信号
        if self._backtest:
            self._bt_bar += 1
            price = float(df["close"].iloc[-1])
            if self._bt_bar % self._bt_interval == 0 or not self._bt_last_signal:
                self._bt_last_signal = self._analyze_with_retry(df, current_position)
            # 复用上次信号，但用当前价格更新 SL/TP
            sig = dict(self._bt_last_signal)
            if sig.get("signal") == "BUY":
                sig["stop_loss"] = price * 0.97
                sig["take_profit"] = price * 1.04
            elif sig.get("signal") == "SELL":
                sig["stop_loss"] = price * 1.03
                sig["take_profit"] = price * 0.96
            else:
                sig["stop_loss"] = price * 0.98
                sig["take_profit"] = price * 1.02
            return sig
        return self._analyze_with_retry(df, current_position)

    # 从交易所获取当前实时持仓
    def get_current_position(self) -> Optional[Dict]:
        if self.exchange is None:
            return None
        try:
            import asyncio
            symbol = self.config["symbol"]
            positions = asyncio.run(self.exchange.fetch_positions([symbol]))
            for pos in positions:
                if pos["symbol"] == symbol and float(pos.get("contracts", 0)) > 0:
                    return {
                        "side": pos["side"],                        # 持仓方向
                        "size": float(pos["contracts"]),             # 持仓数量
                        "entry_price": float(pos.get("entryPrice", 0)),  # 开仓均价
                        "unrealized_pnl": float(pos.get("unrealizedPnl", 0)),  # 未实现盈亏
                        "leverage": float(pos.get("leverage", self.config["leverage"])),  # 杠杆
                        "symbol": pos["symbol"],                    # 交易对
                    }
            return None
        except Exception as e:
            logger.info(f"获取持仓失败: {e}")
            return None

    # 构建包含价格、技术指标、趋势分析的完整数据字典
    def _build_price_data(self, df: pd.DataFrame) -> dict:
        df = self._calc_indicators(df)
        last = df.iloc[-1]
        prev = df.iloc[-2]
        trend = self._get_market_trend(df)
        levels = self._get_support_resistance_levels(df)
        return {
            "price": last["close"],                                    # 当前价格
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # 当前时间
            "high": last["high"],                                      # 最高价
            "low": last["low"],                                        # 最低价
            "volume": last["volume"],                                  # 成交量
            "timeframe": self.config["timeframe"],                     # 时间周期
            "price_change": ((last["close"] - prev["close"]) / prev["close"]) * 100,  # 价格变化率
            "kline_data": df[["timestamp", "open", "high", "low", "close", "volume"]]
            .tail(10)
            .to_dict("records"),                                       # 最近 10 根 K 线
            "technical_data": {                                        # 技术指标数据
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
            "trend_analysis": trend,                                   # 趋势分析结果
            "levels_analysis": levels,                                 # 支撑阻力位
            "full_data": df,                                           # 完整 DataFrame
        }

    # 计算所有技术指标
    def _calc_indicators(self, df):
        return calc_indicators(df)

    def _get_support_resistance_levels(self, df, lookback=20):
        return get_support_resistance_levels(df, lookback)

    def _get_market_trend(self, df):
        return get_market_trend(df)

    # 从 Cryptoracle API 获取市场情绪指标
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
                json=body, headers=headers,
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
                        # 同时拿到多头和空头比率时返回
                        if "CO-A-02-01" in sentiment and "CO-A-02-02" in sentiment:
                            net = sentiment["CO-A-02-01"] - sentiment["CO-A-02-02"]
                            return {
                                "positive_ratio": sentiment["CO-A-02-01"],  # 多头比率
                                "negative_ratio": sentiment["CO-A-02-02"],  # 空头比率
                                "net_sentiment": net,                       # 净情绪值
                                "data_time": period["startTime"],           # 数据时间
                            }
            return None
        except Exception as e:
            logger.info(f"情绪指标获取失败: {e}")
            return None

    def _generate_technical_analysis_text(self, price_data):
        return generate_technical_analysis_text(price_data)

    def _identify_market_state(self, price_data, tech_data):
        return identify_market_state(price_data, tech_data)

    def _calc_dynamic_tp_sl(self, signal, price, market_state, position=None):
        return calc_dynamic_tp_sl(signal, price, market_state, position)

    def _validate_signal(self, ai_signal, price_data, tech_data):
        return validate_signal(ai_signal, price_data, tech_data)

    def _safe_json_parse(self, text):
        return safe_json_parse(text)

    def _fallback_signal(self, price):
        return fallback_signal(price)

    # 带重试机制的分析入口 — 连续失败 3 次后不再重试，直接 fallback
    def _analyze_with_retry(self, df: pd.DataFrame, position=None, max_retries=2) -> Dict:
        if self._consecutive_failures >= 3:
            return self._fallback_signal(float(df["close"].iloc[-1]))

        for attempt in range(max_retries):
            try:
                result = self._analyze(df, position)
                if result and not result.get("is_fallback"):
                    self._consecutive_failures = 0
                    return result
            except Exception:
                pass

        self._consecutive_failures += 1
        if self._consecutive_failures == 1:
            logger.warning(f"DeepSeek API 分析失败，已切换到 fallback 模式")
        if self._consecutive_failures == 3:
            logger.warning("DeepSeek API 连续 3 次失败，后续不再重试")
        return self._fallback_signal(float(df["close"].iloc[-1]))

    # 核心分析逻辑：构建 prompt，调用 AI，解析结果
    def _analyze(self, df: pd.DataFrame, position=None) -> Dict:
        price_data = self._build_price_data(df)
        tech_analysis = self._generate_technical_analysis_text(price_data)

        # 构建 K 线数据文本
        kline_text = f"【最近5根{self.config['timeframe']}K线数据】\n"
        for i, k in enumerate(price_data["kline_data"][-5:]):
            trend = "阳线" if k["close"] > k["open"] else "阴线"
            chg = ((k["close"] - k["open"]) / k["open"]) * 100
            kline_text += f"K线{i + 1}: {trend} 开盘:{k['open']:.2f} 收盘:{k['close']:.2f} 涨跌:{chg:+.2f}%\n"

        # 上次信号参考
        signal_text = ""
        if self.signal_history:
            last = self.signal_history[-1]
            signal_text = f"\n【上次信号】{last.get('signal', 'N/A')} (信心: {last.get('confidence', 'N/A')})"

        # 获取市场情绪
        sent = self._get_sentiment()
        if sent:
            sign = "+" if sent["net_sentiment"] >= 0 else ""
            sentiment_text = f"【市场情绪】乐观{sent['positive_ratio']:.1%} 悲观{sent['negative_ratio']:.1%} 净值{sign}{sent['net_sentiment']:.3f}"
        else:
            sentiment_text = "【市场情绪】数据暂不可用"

        # 当前持仓信息
        cur_pos = position or self.get_current_position()
        if cur_pos:
            # 回测引擎传入的 position 没有 unrealized_pnl，根据当前价格计算
            upnl = cur_pos.get('unrealized_pnl')
            if upnl is None:
                ep = cur_pos['entry_price']
                sz = cur_pos['size']
                upnl = (price_data['price'] - ep) * sz if cur_pos['side'] == 'long' else (ep - price_data['price']) * sz
            pos_text = f"{cur_pos['side']}仓, 数量: {cur_pos['size']}, 盈亏: {upnl:.2f}USDT"
        else:
            pos_text = "无持仓"

        tech_data = price_data.get("technical_data", {})
        market_state = self._identify_market_state(price_data, tech_data)
        suggested = self._calc_dynamic_tp_sl("BUY", price_data["price"], market_state, cur_pos)
        tp_sl_hint = f"建议止损±{suggested['sl_pct'] * 100:.1f}%, 止盈±{suggested['tp_pct'] * 100:.1f}%"

        # 加载 AI 记忆 — 让模型看到自己的历史决策和结果
        from app.services.memory.memory import memory_service
        memory_context = memory_service.build_prompt_context(limit=10)

        # 构建完整的 AI prompt
        symbol = self.config.get("symbol", "BTC/USDT:USDT").split("/")[0]
        prompt = f"""
你是专业的{symbol}永续合约交易分析师，当前周期: {self.config['timeframe']}。

{memory_context}

【核心数据】
价格: ${price_data['price']:,.6f} ({price_data['price_change']:+.2f}%)
市场状态: {market_state['state']} (波动率: {market_state['atr_pct']:.2f}%)
趋势: {price_data['trend_analysis'].get('overall', 'N/A')}
RSI: {price_data['technical_data'].get('rsi', 0):.1f} | MACD: {price_data['trend_analysis'].get('macd', 'N/A')}
持仓: {pos_text}
{signal_text}

{kline_text}

{tech_analysis}

{sentiment_text}

【决策规则】
1. 市场状态"偏多/强上涨" → BUY；"偏空/强下跌" → SELL
2. 震荡+低波动 → HOLD 等待
3. 短线(5m/15m)更激进，小幅趋势即可入场
4. RSI > 75 超买谨慎追多，RSI < 25 超卖谨慎追空
5. 回测模式下，适当增加交易频率以验证策略有效性

【止盈止损】
{tp_sl_hint}
- 盈利 > 5%: 移动止损到保本
- 亏损 > 3%: 果断止损离场

【输出格式】
严格JSON，不要额外文字：
{{
    "signal": "BUY|SELL|HOLD",
    "reason": "核心理由(30字内)",
    "stop_loss": 价格数字,
    "take_profit": 价格数字,
    "confidence": "HIGH|MEDIUM|LOW"
}}
"""
        try:
            # 调用 DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"你是{self.config.get('symbol', '').split('/')[0] if '/' in self.config.get('symbol', '') else ''}永续合约交易员。专注{self.config['timeframe']}周期。严格输出JSON，不加解释。",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
                temperature=self.config.get("temperature", 0.1),
            )

            result = response.choices[0].message.content
            logger.info(f"AI原始回复: {result[:200]}...")

            # 解析 AI 回复中的 JSON
            start_idx = result.find("{")
            end_idx = result.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                signal_data = self._safe_json_parse(result[start_idx:end_idx])
                if signal_data is None:
                    signal_data = self._fallback_signal(price_data["price"])
            else:
                signal_data = self._fallback_signal(price_data["price"])

            # 验证必要字段
            required = ["signal", "reason", "stop_loss", "take_profit", "confidence"]
            if not all(f in signal_data for f in required):
                signal_data = self._fallback_signal(price_data["price"])

            logger.info(f"AI原始信号: {signal_data['signal']} (信心: {signal_data['confidence']})")
            # 用技术指标验证 AI 信号
            signal_data = self._validate_signal(signal_data, price_data, tech_data)
            logger.info(f"验证后信号: {signal_data['signal']} (信心: {signal_data['confidence']})")

            # 非 HOLD 时检查止盈止损合理性
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
                # AI 给出的 TP/SL 不合理时使用动态计算值
                if not sl_ok or not tp_ok:
                    logger.warning(
                        f"AI止盈止损不合理，使用动态计算: SL={dynamic['stop_loss']}, TP={dynamic['take_profit']}"
                    )
                    signal_data["stop_loss"] = dynamic["stop_loss"]
                    signal_data["take_profit"] = dynamic["take_profit"]

            signal_data["timestamp"] = price_data["timestamp"]
            # 记录到历史
            self.signal_history.append(signal_data)
            if len(self.signal_history) > 30:
                self.signal_history.pop(0)

            # 信号统计
            same = sum(1 for s in self.signal_history if s.get("signal") == signal_data["signal"])
            logger.info(f"信号统计: {signal_data['signal']} (最近{len(self.signal_history)}次中出现{same}次)")

            # 连续相同信号告警
            if len(self.signal_history) >= 3:
                last3 = [s["signal"] for s in self.signal_history[-3:]]
                if len(set(last3)) == 1:
                    logger.warning(f"注意：连续3次{signal_data['signal']}信号")

            return signal_data

        except Exception as e:
            logger.info(f"DeepSeek分析失败: {e}")
            return self._fallback_signal(price_data["price"])
