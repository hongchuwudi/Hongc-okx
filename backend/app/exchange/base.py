"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: base.py 交易所基类
描述: 交易所客户端基类 — 线程池 + ccxt 实例管理，OKX/Binance 等交易所的父类

包含:
- 类: BaseExchangeClient — 基类，提供 run_async 和线程池
- 变量: _executor — 全局线程池 (4 workers)
- 函数: parse_okx_error — 解析 ccxt 抛出的 OKX 错误，提取 code/msg
"""

import asyncio
import json
import re
from concurrent.futures import ThreadPoolExecutor

# 全局线程池
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="exchange")

# OKX 常见错误码说明
_OKX_ERROR_ZH = {
    "59000": "操作失败（请先撤销挂单、平仓、停止交易机器人）",
    "51000": "参数错误",
    "50004": "请求超时",
    "50011": "下单频率超限",
    "50013": "系统繁忙",
    "50014": "非交易时段",
    "50026": "取消订单失败（订单可能已成交）",
    "51008": "保证金不足",
}


def parse_okx_error(error: Exception) -> str:
    """
    从 ccxt/OKX 异常中提取可读的错误信息。
    支持 ccxt.NetworkError / ccxt.ExchangeError 等异常类型。
    优先解析 OKX JSON 响应，失败则回退到原始消息。
    Returns: "code=59000 操作失败（请先撤销挂单、平仓、停止交易机器人）"
    """
    raw = str(error)
    # 尝试从异常消息中提取 OKX JSON: okx {"code":"59000",...}
    m = re.search(r'\{[^{]*"code"\s*:\s*"(\d+)"[^}]*"msg"\s*:\s*"([^"]+)"[^}]*\}', raw)
    if m:
        code = m.group(1)
        okx_msg = m.group(2)
        zh = _OKX_ERROR_ZH.get(code, "")
        if zh:
            return f"code={code} {okx_msg} ({zh})"
        return f"code={code} {okx_msg}"
    # 回退：尝试提取 ccxt 格式的异常名和描述
    ccxt_name = type(error).__name__
    # 去掉 "okx " 前缀和多余 JSON
    clean = raw.replace("okx ", "").strip()
    # 如果干净消息还包含大段 JSON，截取 msg 部分
    try:
        data = json.loads(clean)
        if isinstance(data, dict):
            code = str(data.get("code", ""))
            okx_msg = data.get("msg", str(data))
            zh = _OKX_ERROR_ZH.get(code, "")
            if zh:
                return f"code={code} {okx_msg} ({zh})"
            return f"code={code} {okx_msg}"
    except (json.JSONDecodeError, TypeError):
        pass
    return f"{ccxt_name}: {clean[:200]}"


# 交易所客户端基类。封装 ccxt 同步调用为异步。
class BaseExchangeClient:

    # 在线程池中执行同步 ccxt 方法，不阻塞事件循环。
    async def _run(self, fn, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, fn, *args)
