"""
创建时间: 2026-06-06
作者: hongchuwudi
描述: 交易执行服务 — 下单 / 止盈止损 / 仓位管理 / 交易记录查询

包含:
- 类: TradeService — 交易执行 + OKX 成交拉取 + 系统记录查询
- 方法: query_trades         — 查询系统数据库历史交易记录（扁平/分页）
- 方法: query_okx_trades     — 从 OKX 拉取真实成交（分页/方向/时间筛选）
"""

from typing import Optional

from app.core.database import get_sync_session
from app.entities.trading import Trade
from app.core.logger import get_logger

logger = get_logger()


def _safe_entry_price(pos: dict) -> float:
    raw = pos.get("entryPrice")
    if raw is not None and float(raw) > 0:
        return float(raw)
    mark = float(pos.get("markPrice", 0))
    if mark > 0:
        logger.warning(f"OKX entryPrice 无效({raw})，用 markPrice={mark} 兜底")
        return mark
    return 0.0
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
                    "entry_price": _safe_entry_price(pos),   # 开仓均价(含兜底)
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
            return {"action": "open", "side": side, "amount": amount, "order": order, "pnl": 0}

        if position:
            pos_side = position["side"]  # 当前持仓方向 long / short
            if (pos_side == "long" and signal == "BUY") or (pos_side == "short" and signal == "SELL"):
                # 信号方向与持仓方向一致 → 加仓
                side = "buy" if signal == "BUY" else "sell"
                amount = self._calc_contracts(amount_usdt, price, sym, leverage)
                order = await self._exchange.create_order(sym, "market", side, amount)
                # 更新止盈止损为加仓后总仓位
                await self._set_tp_sl(sym, signal, position["size"] + amount, stop_loss, take_profit)
                return {"action": "add", "side": side, "amount": amount, "order": order, "pnl": 0}
            else:
                # 信号方向与持仓方向相反 → 先平仓再开新仓
                close_side = "sell" if pos_side == "long" else "buy"
                close_size = position["size"]
                entry_price = position["entry_price"]
                # 平仓 — 计算平仓盈亏
                await self._exchange.create_order(sym, "market", close_side, close_size)
                pnl = self._calc_close_pnl(pos_side, entry_price, price, close_size, sym)
                # 开新仓
                side = "buy" if signal == "BUY" else "sell"
                amount = self._calc_contracts(amount_usdt, price, sym, leverage)
                order = await self._exchange.create_order(sym, "market", side, amount)
                await self._set_tp_sl(sym, signal, amount, stop_loss, take_profit)
                return {"action": "reverse", "side": side, "amount": amount, "order": order, "pnl": pnl}

        return None

    # 计算平仓盈亏（USDT）
    def _calc_close_pnl(self, pos_side: str, entry_price: float, exit_price: float,
                        contracts: float, symbol: str) -> float:
        market = self._exchange._exchange.market(symbol)
        ct_val = market.get("contractSize", 1)  # 每张合约面值（DOGE=100, BTC=0.01）
        notional = contracts * ct_val  # 持仓总币数
        if pos_side == "long":
            return (exit_price - entry_price) * notional
        else:
            return (entry_price - exit_price) * notional

    # 开仓后挂算法止盈止损单 — 先取消旧单，再分别挂 SL 和 TP
    async def _set_tp_sl(
        self, symbol: str, signal: str, amount: float, sl: float, tp: float
    ) -> None:
        from app.core.exceptions import ExternalServiceError
        # 取消旧算法单 — 失败可容忍（旧单可能已触发/不存在），继续挂新单
        try:
            await self._exchange.cancel_algo_orders(symbol)
        except Exception as e:
            logger.warning(f"取消旧算法单失败(可容忍): {type(e).__name__}: {e}")
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
        # 挂止盈止损单 — 失败必须上抛，否则仓位无保护且调用方无感知
        try:
            await self._exchange.create_algo_order(symbol, close_side, "conditional", amount, sl, sl_side=True)
            await self._exchange.create_algo_order(symbol, close_side, "conditional", amount, tp, sl_side=False)
            logger.info(f"SL/TP 已挂单: SL={sl:.5f} TP={tp:.5f}")
        except Exception as e:
            logger.error(f"SL/TP 挂单失败(仓位无保护!): {type(e).__name__}: {e}")
            raise ExternalServiceError(f"止盈止损挂单失败，仓位无保护: {e}")

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

    # 从 OKX 拉取个人真实成交记录 — 支持分页、方向筛选、时间范围
    @staticmethod
    async def query_okx_trades(
        symbol: str = "DOGE/USDT:USDT",
        limit: int = 100,
        page: int = 1,
        page_size: int = 20,
        side: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        from datetime import datetime, timedelta, timezone
        from app.core.exceptions import BusinessError, ExternalServiceError

        exchange = ExchangeClient()

        # since 时间戳 — 有 start_time 用指定值，否则默认 7 天
        if start_time:
            try:
                since_ms = int(datetime.fromisoformat(start_time).timestamp() * 1000)
            except ValueError:
                raise BusinessError(f"start_time 格式错误: {start_time}")
        else:
            since_ms = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp() * 1000)

        # end_time 转毫秒
        end_ms = None
        if end_time:
            try:
                end_ms = int(datetime.fromisoformat(end_time).timestamp() * 1000)
            except ValueError:
                pass

        try:
            raw = await exchange.fetch_my_trades(symbol, since_ms, limit)
        except Exception as e:
            logger.error(f"OKX fetch_my_trades 失败: {type(e).__name__}: {e}")
            raise ExternalServiceError(f"OKX 成交拉取失败: {e}")

        logger.info(f"OKX 返回 {len(raw)} 笔原始成交")

        # 转换 + 筛选
        all_items = []
        for t in raw:
            amount = t.get("amount")
            price = t.get("price")
            if amount is None or price is None:
                continue
            amount_f = float(amount)
            if amount_f == 0:
                continue
            price_f = float(price)

            trade_side = str(t.get("side", ""))
            ts = t.get("timestamp", 0)

            # 时间范围过滤
            if end_ms and ts and ts > end_ms:
                continue
            # 方向过滤
            if side and trade_side != side:
                continue

            fee_info = t.get("fee") or {}
            cost_val = t.get("cost")
            dt = t.get("datetime") or ""
            if not dt and ts:
                dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()

            # OKX fills-history 原始响应在 info 中，pnl 字段名可能是 pnl 或 fillPnl
            info = t.get("info", {}) or {}
            raw_pnl = None
            if isinstance(info, dict):
                raw_pnl = info.get("pnl") or info.get("fillPnl")
            if raw_pnl is None:
                raw_pnl = t.get("pnl")

            all_items.append({
                "id": str(t.get("id", "")),
                "order_id": str(t.get("order", "")),
                "timestamp": str(dt),
                "symbol": str(t.get("symbol", symbol)),
                "side": "BUY" if trade_side == "buy" else "SELL",
                "price": price_f,
                "amount": amount_f,
                "cost": float(cost_val) if cost_val else price_f * amount_f,
                "fee": float(fee_info.get("cost", 0)) if fee_info else 0.0,
                "fee_currency": str(fee_info.get("currency", "USDT")) if fee_info else "USDT",
                "role": str(t.get("takerOrMaker", "")),
                "type": str(t.get("type", "")),
                "pnl": float(raw_pnl) if raw_pnl else 0.0,
            })

        # 分页
        total = len(all_items)
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0
        safe_page = max(1, min(page, max(1, total_pages))) if total_pages > 0 else 1
        start = (safe_page - 1) * page_size
        paged = all_items[start:start + page_size]

        return {
            "data": paged,
            "total": total,
            "page": safe_page,
            "page_size": page_size,
            "total_pages": total_pages,
            "symbol": symbol,
        }
