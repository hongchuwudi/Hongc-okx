"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: base.py 交易所基类
描述: 交易所客户端基类 — 线程池 + ccxt 实例管理，OKX/Binance 等交易所的父类

包含:
- 类: BaseExchangeClient — 基类，提供 run_async 和线程池
- 变量: _executor — 全局线程池 (4 workers)
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

# 全局线程池
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="exchange")


class BaseExchangeClient:
    """交易所客户端基类。封装 ccxt 同步调用为异步。"""

    async def _run(self, fn, *args):
        """在线程池中执行同步 ccxt 方法，不阻塞事件循环。"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, fn, *args)
