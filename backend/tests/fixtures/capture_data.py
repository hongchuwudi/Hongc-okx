"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: capture_data.py 行情数据采集
描述: 拉取真 OKX 行情数据存为 JSON，供测试复用

用法: python tests/fixtures/capture_data.py
"""

import json
import asyncio
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


async def capture():
    """拉取 DOGE/USDT 1分钟 K线和 ticker，存为 JSON。"""
    from app.exchange.client import ExchangeClient

    exchange = ExchangeClient()
    symbol = "DOGE/USDT:USDT"

    print(f"拉取 {symbol} K线数据...")
    df = await exchange.fetch_ohlcv(symbol, "1m", 200)
    ticker = await exchange.fetch_ticker(symbol)
    balance = await exchange.fetch_balance()
    positions = await exchange.fetch_positions([symbol])

    # 存 K 线
    kline_path = FIXTURES_DIR / "okx_kline.json"
    kline_path.write_text(df.to_json(orient="records", date_format="iso"), encoding="utf-8")
    print(f"K线 ({len(df)}条) → {kline_path}")

    # 存 ticker
    ticker_path = FIXTURES_DIR / "okx_ticker.json"
    ticker_path.write_text(json.dumps(ticker, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Ticker → {ticker_path}")

    # 存持仓
    pos_path = FIXTURES_DIR / "okx_position.json"
    pos_path.write_text(json.dumps(positions, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"持仓 ({len(positions)}个) → {pos_path}")

    # 存账户
    account_path = FIXTURES_DIR / "okx_account.json"
    account_path.write_text(json.dumps(balance, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"账户 → {account_path}")

    print("采集完毕")


if __name__ == "__main__":
    asyncio.run(capture())
