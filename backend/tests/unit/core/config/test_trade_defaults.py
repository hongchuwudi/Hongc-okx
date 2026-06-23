"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_trade_defaults.py TradeConfig 默认值测试
描述: 验证 TradeConfig 默认参数
"""

from app.core.config import config


def test_trade_config_has_expected_defaults():
    t = config.trade
    assert t.symbol == "DOGE/USDT:USDT", f"默认交易对, 实际 {t.symbol}"
    assert t.leverage == 10, f"默认杠杆 10x, 实际 {t.leverage}x"
    assert t.tick_interval_seconds == 360, f"默认 tick 间隔 360s, 实际 {t.tick_interval_seconds}s"
    assert t.order_amount > 0, "下单金额应大于 0"
    assert t.max_daily_drawdown_pct > 0, "日回撤上限应大于 0"
    assert t.max_daily_loss_usdt > 0, "日亏损上限应大于 0"
