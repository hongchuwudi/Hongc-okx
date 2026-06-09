"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: trade.py 交易服务
描述: 交易执行服务 — 下单、止盈止损、仓位管理 + 交易记录查询

包含:
- 类: TradeService — 交易执行服务，封装 OKX 订单操作
- 函数: query_trades — 查询历史交易记录（扁平/分页）
"""

from typing import Optional

from app.database import get_sync_session
from app.entities.trading import Trade
from app.exchange.client import ExchangeClient


# 交易执行服务 封装 OKX 订单操作，处理仓位计算和执行逻辑。
class TradeService:

    def __init__(self, exchange: ExchangeClient, config: dict | None = None):
        # 交易所客户端实例
        self._exchange = exchange
        # 交易配置字典
        self._config = config or {}
        # 交易对符号
        self._symbol = self._config.get("symbol")
        # 杠杆倍数
        self._leverage = self._config.get("leverage", 1)

    # 获取当前持仓，无持仓时返回 None
    async def get_position(self, symbol: str | None = None) -> Optional[dict]:
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

    # 执行交易：根据信号开仓/平仓/反向
    async def execute(
        self,
        signal: str,
        price: float,
        stop_loss: float,
        take_profit: float,
        amount_usdt: float = 1.0,
        leverage: int = 10,
    ) -> Optional[dict]:
        sym = self._symbol
        position = await self.get_position(sym)

        if signal == "HOLD":
            return {"action": "hold", "reason": "观望信号"}

        if position is None and signal in ("BUY", "SELL"):
            # 无持仓 → 开仓
            side = "buy" if signal == "BUY" else "sell"
            amount = self._calc_contracts(amount_usdt, price, sym, leverage)
            order = await self._exchange.create_order(sym, "market", side, amount)
            # 开仓后设置算法止盈止损单
            await self._set_tp_sl(sym, signal, amount, stop_loss, take_profit)
            return {"action": "open", "side": side, "amount": amount, "order": order}

        if position:
            pos_side = position["side"]  # 当前持仓方向 long / short
            if (pos_side == "long" and signal == "BUY") or (pos_side == "short" and signal == "SELL"):
                # 信号方向与持仓方向一致 → 加仓
                side = "buy" if signal == "BUY" else "sell"
                amount = self._calc_contracts(amount_usdt, price, sym, leverage)
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
                amount = self._calc_contracts(amount_usdt, price, sym, leverage)
                order = await self._exchange.create_order(sym, "market", side, amount)
                await self._set_tp_sl(sym, signal, amount, stop_loss, take_profit)
                return {"action": "reverse", "side": side, "amount": amount, "order": order}

        return None

    # 开仓后挂算法止盈止损单 — 先取消旧单，再分别挂 SL 和 TP
    async def _set_tp_sl(
        self, symbol: str, signal: str, amount: float, sl: float, tp: float
    ) -> None:
        from app.core.logger import get_logger
        _log = get_logger()
        try:
            await self._exchange.cancel_algo_orders(symbol)
        except Exception:
            pass
        close_side = "sell" if signal == "BUY" else "buy"
        try:
            ticker = await self._exchange.fetch_ticker(symbol)
            last = ticker.get("last", 0) if ticker else 0
        except Exception:
            last = 0
        if signal == "SELL":
            sl = max(sl, last * 1.001) if last else sl
            tp = min(tp, last * 0.999) if last else tp
        else:
            sl = min(sl, last * 0.999) if last else sl
            tp = max(tp, last * 1.001) if last else tp
        try:
            await self._exchange.create_algo_order(symbol, close_side, "conditional", amount, sl, sl_side=True)
            await self._exchange.create_algo_order(symbol, close_side, "conditional", amount, tp, sl_side=False)
            _log.info(f"SL/TP 已挂单: SL={sl:.5f} TP={tp:.5f}")
        except Exception as e:
            _log.error(f"SL/TP 挂单失败(仓位无保护!): {e}")

    # 更新持仓的止盈止损算法单（取消旧单 + 挂新单）
    async def update_tp_sl(
        self, symbol: str, signal: str, amount: float,
        stop_loss: float, take_profit: float,
    ) -> dict:
        await self._set_tp_sl(symbol, signal, amount, stop_loss, take_profit)
        return {"stop_loss": stop_loss, "take_profit": take_profit}

    # 将 USDT 保证金金额转换为 OKX 合约张数（含杠杆）
    def _calc_contracts(self, usdt: float, price: float, symbol: str, leverage: int = 10) -> float:
        market = self._exchange._exchange.market(symbol)
        ct_val = market["contractSize"]  # OKX 实际合约面值（DOGE=100, ETH=0.1, BTC=0.01）
        notional = usdt * leverage  # 保证金 → 名义价值
        contracts = notional / (price * ct_val)
        # 确保合约张数至少为 1 张的最小单位（precision=0 的品种向下舍会变 0）
        min_contract = market["limits"]["amount"]["min"] or 0.01
        prec = market["precision"]["amount"]
        if prec is not None and prec <= 0:
            min_contract = max(min_contract, 1.0)
        contracts = max(min_contract, contracts)
        return float(self._exchange._exchange.amount_to_precision(symbol, contracts))

    # Trade ORM → dict 转换
    @staticmethod
    def _trade_to_dict(t: Trade) -> dict:
        return {
            "id": t.id, "timestamp": t.timestamp.isoformat() if t.timestamp else "",
            "signal": t.signal, "price": t.price, "amount": t.amount,
            "confidence": t.confidence, "reason": t.reason, "pnl": t.pnl,
        }

    # 查询历史交易记录 — ?limit=N 返回扁平数组，?page=&page_size= 返回分页对象
    @staticmethod
    def query_trades(limit: int | None = None, page: int = 1, page_size: int = 20) -> list[dict] | dict:
        session = get_sync_session()
        try:
            if limit is not None:
                trades = (
                    session.query(Trade)
                    .order_by(Trade.timestamp.desc()).limit(limit).all()
                )
                return [TradeService._trade_to_dict(t) for t in reversed(trades)]

            total = session.query(Trade).count()
            offset = (page - 1) * page_size
            trades = (
                session.query(Trade)
                .order_by(Trade.timestamp.desc()).offset(offset).limit(page_size).all()
            )
            return {
                "data": [TradeService._trade_to_dict(t) for t in reversed(trades)],
                "page": page, "page_size": page_size,
                "total": total,
                "total_pages": max(1, (total + page_size - 1) // page_size),
            }
        finally:
            session.close()
