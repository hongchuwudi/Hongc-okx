"""定时调度服务 — 替代原 wait_for_next_period()"""

import asyncio
import time
from datetime import datetime
from typing import Callable, Coroutine

from app.database import get_redis


class SchedulerService:
    """异步定时调度器

    支持:
    - 每 N 秒执行一次
    - 对齐整点 15 分钟（原逻辑兼容）
    - Redis 分布式锁防重执行
    """

    def __init__(self, interval_seconds: int = 60, align_to_quarter: bool = True):
        self._interval = interval_seconds
        self._align_to_quarter = align_to_quarter
        self._running = False

    async def run_loop(
        self, callback: Callable[[], Coroutine]
    ) -> None:
        """启动调度循环"""
        # 启动时清除可能残留的旧锁
        redis = await get_redis()
        await redis.delete("lock:scheduler:tick")

        self._running = True
        while self._running:
            await self._wait_for_next()
            # 分布式锁防重
            if not await self._acquire_lock():
                print("⚠ 调度锁被占用，跳过本次 tick")
                continue
            try:
                await callback()
            except Exception as e:
                print(f"⚠ Tick 执行异常: {e}")
            finally:
                await self._release_lock()

    async def stop(self) -> None:
        self._running = False

    async def _wait_for_next(self) -> None:
        """等待到下一个调度时刻"""
        now_ts = time.time()
        if self._align_to_quarter:
            # 对齐到 interval 的整倍数（基于 Unix epoch）
            # interval=60  → 对齐整分钟 (xx:xx:00)
            # interval=900 → 对齐 15 分钟 (xx:00/15/30/45)
            next_ts = ((now_ts // self._interval) + 1) * self._interval
        else:
            next_ts = now_ts + self._interval
        sleep_seconds = next_ts - now_ts
        if sleep_seconds > 0:
            next_dt = datetime.fromtimestamp(next_ts)
            print(f"⏰ 下次执行: {next_dt.strftime('%H:%M:%S')} (等待 {sleep_seconds:.0f}s)")
            await asyncio.sleep(sleep_seconds)

    async def _acquire_lock(self) -> bool:
        """Redis SETNX 分布式锁"""
        redis = await get_redis()
        acquired = await redis.set(
            "lock:scheduler:tick", "1", nx=True, ex=self._interval
        )
        return bool(acquired)

    async def _release_lock(self) -> None:
        redis = await get_redis()
        await redis.delete("lock:scheduler:tick")
