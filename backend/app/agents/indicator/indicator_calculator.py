"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: indicator_calculator.py 指标计算器
描述: 对 OHLCV DataFrame 计算全部技术指标，返回增强后的 DataFrame

包含:
- 函数: calculate_all — 计算全部技术指标并返回增强 DataFrame
- 函数: latest_indicators — 返回最后一根 K 线的指标快照字典

技术指标列表:
    1. 移动平均线 (SMA) — 5/20/50 周期
    2. 指数移动平均 (EMA) — 12/26 周期（用于 MACD）
    3. MACD 及其信号线、柱状图
    4. 相对强弱指数 (RSI) — 14 周期
    5. 布林带 (Bollinger Bands) — 20 周期，2 倍标准差
    6. 成交量移动平均和成交量比率
"""

import pandas as pd


def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
    """
    对 OHLCV DataFrame 计算全部技术指标，返回增强后的 DataFrame。
    参数:
        df : pandas.DataFrame，必须包含 'open', 'high', 'low', 'close', 'volume' 列。
    返回:
        pandas.DataFrame，包含原始列加上所有计算出的指标列。
        指标列命名：sma_5, sma_20, sma_50, ema_12, ema_26, macd, macd_signal,
                   macd_histogram, rsi, bb_middle, bb_upper, bb_lower, bb_position,
                   volume_ma, volume_ratio。
    注意:
        - 计算时复制了一份数据，避免修改原始 DataFrame。
        - 使用 bfill() 和 ffill() 填充因滚动窗口产生的 NaN，保证结果完整。
    """
    # 复制数据以避免修改原 DataFrame
    df = df.copy()

    # ---------- 移动平均线 (Simple Moving Average) ----------
    # 使用 rolling 窗口计算简单移动平均，min_periods=1 使窗口不足时仍用现有值计算
    df["sma_5"] = df["close"].rolling(window=5, min_periods=1).mean()    # 5 周期均线（短线）
    df["sma_20"] = df["close"].rolling(window=20, min_periods=1).mean()   # 20 周期均线（中短线）
    df["sma_50"] = df["close"].rolling(window=50, min_periods=1).mean()   # 50 周期均线（中线）

    # ---------- 指数移动平均 (Exponential Moving Average) ----------
    # ewm(span) 计算指数加权移动平均，span 为周期数，可视为类似 EMA 的平滑参数
    df["ema_12"] = df["close"].ewm(span=12).mean()   # 12 周期 EMA（快线）
    df["ema_26"] = df["close"].ewm(span=26).mean()   # 26 周期 EMA（慢线）

    # ---------- MACD (Moving Average Convergence Divergence) ----------
    # MACD 线 = 快线 - 慢线
    df["macd"] = df["ema_12"] - df["ema_26"]
    # 信号线 = MACD 的 9 周期 EMA
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    # MACD 柱状图 = MACD 线 - 信号线
    df["macd_histogram"] = df["macd"] - df["macd_signal"]

    # ---------- RSI (Relative Strength Index) ----------
    # 计算价格变动
    delta = df["close"].diff()
    # 分别提取正向变动和负向变动
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()   # 平均上涨幅度
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean() # 平均下跌幅度（转为正值）
    # 相对强度 RS = 平均上涨 / 平均下跌（避免除零，loss 可能为 0）
    rs = gain / loss
    # RSI = 100 - (100 / (1 + RS))
    df["rsi"] = 100.0 - (100.0 / (1.0 + rs))

    # ---------- 布林带 (Bollinger Bands) ----------
    # 中轨 = 20 周期 SMA
    df["bb_middle"] = df["close"].rolling(20).mean()
    # 标准差（20 周期）
    bb_std = df["close"].rolling(20).std()
    # 上轨 = 中轨 + 2 * 标准差
    df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
    # 下轨 = 中轨 - 2 * 标准差
    df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
    # 布林带位置：当前价格在下轨～上轨中的相对位置（0 在下轨，1 在上轨）
    # 加 1e-10 防止分母为 0 导致除零错误
    df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + 1e-10)

    # ---------- 成交量指标 ----------
    # 成交量 20 周期移动平均
    df["volume_ma"] = df["volume"].rolling(20).mean()
    # 成交量比率 = 当前成交量 / 均量（用于判断放量/缩量，均量为 0 时替换为 1）
    df["volume_ratio"] = df["volume"] / df["volume_ma"].replace(0, 1)

    # 填充缺失值：先向后填充（bfill），再向前填充（ffill）
    # 保证每行都有数据，避免后续策略调用时出现 NaN
    df = df.bfill().ffill()
    return df


def latest_indicators(df: pd.DataFrame) -> dict:
    """
    返回最后一根 K 线的指标快照字典。

    该函数假定传入的 df 已经过 calculate_all() 处理，包含所有指标列。
    如果某些指标列不存在，将返回 0 作为默认值。

    参数:
        df : pandas.DataFrame，必须包含指标列（建议由 calculate_all 生成）。

    返回:
        dict，包含以下键值对（均为 float）：
            - sma_5        : 5 周期简单移动平均
            - sma_20       : 20 周期简单移动平均
            - sma_50       : 50 周期简单移动平均
            - rsi          : 14 周期相对强弱指数（0~100）
            - macd         : MACD 线
            - macd_signal  : MACD 信号线
            - macd_histogram : MACD 柱状图（正负表示多头/空头力量）
            - bb_upper     : 布林带上轨
            - bb_lower     : 布林带下轨
            - bb_position  : 价格在布林带中的位置（0~1）
            - volume_ratio : 成交量比率（>1 放量，<1 缩量）

    用途:
        常用于策略决策的即时数据输入。
    """
    # 取最后一行的数据（pandas Series）
    row = df.iloc[-1]
    # 使用 get 方法，若列不存在或值为 NaN/None，则返回 0.0
    # 注意：if row.get(...) or 0 会正确将 None/NaN 转为 0，但注意若值为 0 则也为 False，但这里无妨
    return {
        "sma_5": float(row.get("sma_5", 0) or 0),
        "sma_20": float(row.get("sma_20", 0) or 0),
        "sma_50": float(row.get("sma_50", 0) or 0),
        "rsi": float(row.get("rsi", 0) or 0),
        "macd": float(row.get("macd", 0) or 0),
        "macd_signal": float(row.get("macd_signal", 0) or 0),
        "macd_histogram": float(row.get("macd_histogram", 0) or 0),
        "bb_upper": float(row.get("bb_upper", 0) or 0),
        "bb_lower": float(row.get("bb_lower", 0) or 0),
        "bb_position": float(row.get("bb_position", 0) or 0),
        "volume_ratio": float(row.get("volume_ratio", 0) or 0),
    }