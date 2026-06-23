"""
K线数据采集 — 拉取全部 OKX 周期，失败跳过继续

用法:
  python tools/fetch_kline_data.py
  python tools/fetch_kline_data.py --symbol DOGE/USDT:USDT
  python tools/fetch_kline_data.py --tf 1h
"""

import os, sys, json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import ccxt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
KLINE_ROOT = ROOT / "data" / "kline"
KLINE_ROOT.mkdir(parents=True, exist_ok=True)

# 默认实盘，--mode demo 切模拟盘
DATA_DIR = None  # 运行时根据 mode 设置

SYMBOLS = [
    "BTC/USDT:USDT", "ETH/USDT:USDT", "DOGE/USDT:USDT", "SOL/USDT:USDT",
    "XRP/USDT:USDT", "BNB/USDT:USDT", "ADA/USDT:USDT", "AVAX/USDT:USDT",
]

ALL_TF = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w"]

# OKX 实时 K 线最多 1440 根，超过走历史 K 线（慢），按需限制
MAX_BARS = 2000

def _make_ex(sandbox=False):
    ex = ccxt.okx({
        "hostname": "www.okx.cab", "enableRateLimit": True,
        "verify": False, "options": {"defaultType": "swap"},
        "timeout": 30000,
    })
    proxy = os.getenv("HTTPS_PROXY")
    if proxy:
        ex.https_proxy = proxy
    if sandbox:
        ex.set_sandbox_mode(True)
    return ex


def fetch_all(ex, symbol, tf, max_bars):
    """分页拉取。长周期限制起点避免超出数据范围。"""
    tf_ms = _tf_ms(tf) * 60 * 1000
    since = ex.milliseconds() - max_bars * tf_ms
    # 长周期数据不会太久远，限制最早 2024-01-01
    min_since = ex.parse8601("2024-01-01T00:00:00Z")
    since = max(since, min_since)

    all_data = []
    while since < ex.milliseconds():
        data = ex.fetch_ohlcv(symbol, tf, since, 300)
        if not data:
            break
        all_data.extend(data)
        since = data[-1][0] + tf_ms
        if len(data) < 300:
            break

    return all_data[-max_bars:] if len(all_data) > max_bars else all_data


def _tf_ms(tf):
    return {"1m":1,"3m":3,"5m":5,"15m":15,"30m":30,"1h":60,"2h":120,"4h":240,"6h":360,"12h":720,"1d":1440,"1w":10080}.get(tf, 60)


def save_csv(symbol, tf, raw):
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    name = symbol.split("/")[0].lower()
    s = str(df["timestamp"].iloc[0]).replace(" ", "_").replace(":", "")
    e = str(df["timestamp"].iloc[-1]).replace(" ", "_").replace(":", "")
    subdir = DATA_DIR / name
    subdir.mkdir(parents=True, exist_ok=True)
    fpath = subdir / f"{name}_{tf}_{s}_{e}.csv"
    df.to_csv(fpath, index=False)
    return fpath


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--symbol")
    p.add_argument("--tf")
    p.add_argument("--max-bars", type=int, default=MAX_BARS)
    p.add_argument("--mode", choices=["live", "demo"], default="live")
    args = p.parse_args()

    sandbox = args.mode == "demo"
    data_dir = KLINE_ROOT / args.mode
    data_dir.mkdir(parents=True, exist_ok=True)
    global DATA_DIR
    DATA_DIR = data_dir

    symbols = [args.symbol] if args.symbol else SYMBOLS
    tfs = [args.tf] if args.tf else ALL_TF
    total = len(symbols) * len(tfs)

    print(f"OKX K线采集 | 币种:{len(symbols)} 周期:{len(tfs)} 文件:{total}")
    print(f"模式: {args.mode}  代理: {os.getenv('HTTPS_PROXY', '无')}")
    print(f"输出: {data_dir}")
    print("=" * 50)

    ex = _make_ex(sandbox=sandbox)
    ok, fail = 0, 0

    for i, sym in enumerate(symbols):
        name = sym.split("/")[0].lower()
        for tf in tfs:
            n = i * len(tfs) + tfs.index(tf) + 1
            print(f"  [{n}/{total}] {name:5s} {tf:4s}", end=" ", flush=True)

            try:
                raw = fetch_all(ex, sym, tf, args.max_bars)
            except Exception as e:
                print(f"X {type(e).__name__}")
                fail += 1
                continue

            if not raw:
                print("- 无数据")
                fail += 1
                continue

            try:
                fpath = save_csv(sym, tf, raw)
                df = pd.read_csv(fpath)
                s = df["timestamp"].iloc[0]
                e = df["timestamp"].iloc[-1]
                print(f"{len(raw):5d}根  {s} ~ {e}")
                ok += 1
            except Exception as e:
                print(f"X 保存失败: {e}")
                fail += 1

    print(f"\n完成: {ok} 成功, {fail} 失败 -> {DATA_DIR}")


if __name__ == "__main__":
    main()
