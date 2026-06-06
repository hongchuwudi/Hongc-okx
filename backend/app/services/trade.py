"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: trade.py 中文名
描述: 交易执行服务 — 下单、止盈止损、仓位管理

包含:
- 类: TradeService — 交易执行服务，封装 OKX 订单操作
"""

from typing import Optional

from app.exchange.client import ExchangeClient


class TradeService:
    """交易执行服务

    封装 OKX 订单操作，处理仓位计算和执行逻辑。
    """

    def __init__(self, exchange: ExchangeClient, config: dict | None = None):
        # 交易所客户端实例
        self._exchange = exchange
        # 交易配置字典
        self._config = config or {}
        # 交易对符号
        self._symbol = self._config.get("symbol", "BTC/USDT:USDT")
        # 杠杆倍数
        self._leverage = self._config.get("leverage", 1)

    async def get_position(self, symbol: str | None = None) -> Optional[dict]:
        """获取当前持仓，无持仓时返回 None"""
        sym = symbol or self._symbol
        positions = await self._exchange.fetch_positions([sym])
        for pos in positions:
            if pos["symbol"] == sym and float(pos.get("contracts", 0)) > 0:
                return {
                    "side": pos["side"],                    # 持仓方向 long/short
                    "size": float(pos["contracts"]),         # 持仓数量
                    "entry_price": float(pos.get("entryPrice", 0)),  # 开仓均价
                    "unrealized_pnl": float(pos.get("unrealizedPnl", 0)),  # 未实现盈亏
                }
        return None

    async def execute(
        self,
        signal: str,
        price: float,
        stop_loss: float,
        take_profit: float,
        amount_usdt: float = 1.0,
    ) -> Optional[dict]:
        """执行交易：根据信号开仓/平仓/反向"""
        sym = self._symbol
        position = await self.get_position(sym)

        if signal == "HOLD":
            return {"action": "hold", "reason": "观望信号"}

        if position is None and signal in ("BUY", "SELL"):
            # 无持仓 → 开仓
            side = "buy" if signal == "BUY" else "sell"
            amount = self._calc_contracts(amount_usdt, price, sym)
            order = await self._exchange.create_order(sym, "market", side, amount)
            # 开仓后设置算法止盈止损单
            await self._set_tp_sl(sym, signal, amount, stop_loss, take_profit)
            return {"action": "open", "side": side, "amount": amount, "order": order}

        if position:
            pos_side = position["side"]  # 当前持仓方向 long / short
            if (pos_side == "long" and signal == "BUY") or (pos_side == "short" and signal == "SELL"):
                # 信号方向与持仓方向一致 → 加仓
                side = "buy" if signal == "BUY" else "sell"
                amount = self._calc_contracts(amount_usdt, price, sym)
                order = await self._exchange.create_order(sym, "market", side, amount)
                # 更新止盈止损为加仓后总仓位
                await self._set_tp_sl(sym, signal, position["size"] + amount, stop_loss, take_profit)
                return {"action": "add", "side": side, "amount": amount, "order": order}
            else:
                # 信号方向与持仓方向相反 → 先平仓再开新仓
                close_side = "sell" if pos_side == "long" else "buy"
                await self._exchange.create_order(sym, "market", close_side, position["size"])
                # 平仓后开新仓
                side = "buy" if signal == "BUY" else "sell"
                amount = self._calc_contracts(amount_usdt, price, sym)
                order = await self._exchange.create_order(sym, "market", side, amount)
                await self._set_tp_sl(sym, signal, amount, stop_loss, take_profit)
                return {"action": "reverse", "side": side, "amount": amount, "order": order}

        return None

    async def _set_tp_sl(
        self, symbol: str, signal: str, amount: float, sl: float, tp: float
    ) -> None:
        """开仓后挂算法止盈止损单 — 先取消旧单再挂新单，止损方向与持仓方向相反"""
        # 先取消旧的算法订单
        try:
            await self._exchange.cancel_algo_orders(symbol)
        except Exception:
            pass
        close_side = "sell" if signal == "BUY" else "buy"
        # 挂止损单：价格触发即市价平仓
        await self._exchange.create_algo_order(symbol, close_side, "conditional", amount, sl)
        # 挂止盈单：价格触发即市价平仓
        await self._exchange.create_algo_order(symbol, close_side, "conditional", amount, tp, tp)

    async def update_tp_sl(
        self, symbol: str, signal: str, amount: float,
        stop_loss: float, take_profit: float,
    ) -> dict:
        """更新持仓的止盈止损算法单（取消旧单 + 挂新单）"""
        await self._set_tp_sl(symbol, signal, amount, stop_loss, take_profit)
        return {"stop_loss": stop_loss, "take_profit": take_profit}

    def _calc_contracts(self, usdt: float, price: float, symbol: str) -> float:
        """将 USDT 金额转换为合约张数（最小 0.01 张）"""
        contract_size = 0.01 if "BTC" in symbol else 0.1
        contracts = usdt / (price * contract_size)
        return max(0.01, round(contracts, 2))
