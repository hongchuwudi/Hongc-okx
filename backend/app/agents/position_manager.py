"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: position_manager.py 动态追踪止损止盈管理
描述: 动态持仓管理器 — 每 tick 更新追踪止损/止盈

包含:
- 类: PositionManager — 动态持仓管理，追踪止损、ATR 自适应止盈、去抖更新
- 函数: update — 评估并更新持仓的止盈止损
- 函数: _calc_trailing_stop — 计算追踪止损价位
- 函数: _calc_adaptive_tp — 根据波动率调整止盈目标
"""

from app.logger import get_logger

# 全局日志记录器
logger = get_logger()


class PositionManager:
    """动态持仓管理。

    每 tick 运行，包括 HOLD tick：
    1. 追踪止损 — 盈利到阈值后锁定利润
    2. ATR 调整 — 根据当前波动率调整 TP/SL 宽度
    3. 去抖更新 — 变化 < 0.1% 时跳过（避免频繁 API 调用）
    """

    def __init__(self, exchange, symbol: str = "BTC/USDT:USDT"):
        # 交易所客户端实例
        self._exchange = exchange
        # 交易对符号
        self._symbol = symbol
        # 上次设置的止损价（用于去抖比较）
        self._last_sl: float | None = None
        # 上次设置的止盈价（用于去抖比较）
        self._last_tp: float | None = None

    # ── 主入口 ────────────────────────────────────────────

    async def update(
        self,
        position: dict | None,
        current_price: float,
        atr_pct: float,
        current_sl: float,
        current_tp: float,
    ) -> dict:
        """评估并更新持仓的止盈止损。

        Returns: {updated: bool, stop_loss: float, take_profit: float, reason: str}
        """
        # 无持仓时跳过
        if not position or not position.get("side") or position.get("size", 0) <= 0:
            return {"updated": False, "stop_loss": current_sl, "take_profit": current_tp, "reason": "无持仓"}

        side = position["side"]
        entry = float(position.get("entry_price", current_price))  # 入场价
        size = float(position.get("size", 0))  # 持仓张数
        unrealized = float(position.get("unrealized_pnl", 0))  # 浮动盈亏

        # 计算盈亏百分比（基于 1 倍杠杆估算）
        if entry > 0 and size > 0:
            margin = entry * size * 0.01  # 1 倍杠杆估算保证金
            profit_pct = (unrealized / margin * 100) if margin > 0 else 0
        else:
            profit_pct = 0

        # 计算新的止盈止损
        new_sl = self._calc_trailing_stop(side, entry, current_price, profit_pct, current_sl, atr_pct)
        new_tp = self._calc_adaptive_tp(side, entry, current_price, profit_pct, current_tp, atr_pct)

        # 去抖：变化 < 0.1% 不更新（避免频繁 API 调用）
        sl_changed = self._last_sl is None or abs(new_sl - self._last_sl) / self._last_sl > 0.001
        tp_changed = self._last_tp is None or abs(new_tp - self._last_tp) / self._last_tp > 0.001

        if not sl_changed and not tp_changed:
            return {"updated": False, "stop_loss": current_sl, "take_profit": current_tp, "reason": "无显著变化"}

        # 更新 OKX 算法单（止盈止损挂单）
        try:
            okx_symbol = self._symbol.replace("/", "-").replace(":USDT", "-SWAP")
            close_side = "sell" if side == "long" else "buy"

            # 取消旧算法单
            await self._exchange.cancel_algo_orders(self._symbol)

            # 挂新止损单
            await self._exchange.create_algo_order(
                self._symbol, close_side, "conditional", size, new_sl
            )
            # 挂新止盈单
            await self._exchange.create_algo_order(
                self._symbol, close_side, "conditional", size, new_tp, new_tp
            )

            # 记录最新值
            self._last_sl = new_sl
            self._last_tp = new_tp

            logger.info(
                f"持仓管理: 止损→{new_sl:.2f} 止盈→{new_tp:.2f} "
                f"(盈亏{profit_pct:+.1f}%)"
            )
            return {
                "updated": True,
                "stop_loss": new_sl,
                "take_profit": new_tp,
                "reason": f"追踪止损更新 (盈亏{profit_pct:+.1f}%)",
            }

        except Exception as e:
            logger.error(f"持仓管理失败: {e}")
            return {"updated": False, "stop_loss": current_sl, "take_profit": current_tp, "reason": str(e)}

    # ── 追踪止损计算 ───────────────────────────────────────

    def _calc_trailing_stop(
        self, side: str, entry: float, price: float,
        profit_pct: float, current_sl: float, atr_pct: float,
    ) -> float:
        """计算追踪止损价位。

        多头: SL < entry（价格下跌触发止损）
        空头: SL > entry（价格上涨触发止损）

        规则:
        - 盈利 > 5%: 移动到保本+1%
        - 盈利 > 2%: 追踪到盈利-1%（保护一半利润）
        - 否则: 保持当前 SL 或 ATR 默认
        """
        if side == "long":
            if profit_pct > 5:
                return max(current_sl, entry * 1.01)  # 保本+1%
            elif profit_pct > 2:
                return max(current_sl, price * 0.99)  # 锁定1%利润
            return current_sl  # 保持当前 SL
        else:  # short
            if profit_pct > 5:
                return min(current_sl, entry * 0.99)  # 保本-1%
            elif profit_pct > 2:
                return min(current_sl, price * 1.01)  # 锁定1%利润
            return current_sl

    # ── 自适应止盈计算 ─────────────────────────────────────

    def _calc_adaptive_tp(
        self, side: str, entry: float, price: float,
        profit_pct: float, current_tp: float, atr_pct: float,
    ) -> float:
        """根据波动率调整止盈目标。

        高波动(ATR>3%): 目标更远
        低波动(ATR<1%): 目标更近
        """
        # 根据 ATR 确定止盈倍数
        if atr_pct > 3:
            mult = 6.0  # 高波动：6倍 ATR
        elif atr_pct < 1:
            mult = 3.0  # 低波动：3倍 ATR
        else:
            mult = 5.0  # 正常：5倍 ATR

        if side == "long":
            return price * (1 + atr_pct / 100 * mult)
        else:
            return price * (1 - atr_pct / 100 * mult)
