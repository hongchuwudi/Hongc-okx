"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_setup_console.py setup_logging 控制台输出测试
描述: 验证 setup_logging 配置控制台 handler
"""

import logging
from app.core.logger import setup_logging, shutdown_logging


def test_setup_logging_adds_console_handler():
    logger = setup_logging()
    assert len(logger.handlers) >= 2, (
        f"期望至少有 file + console 两个 handler, 实际 {len(logger.handlers)}"
    )
    # 验证至少有一个 StreamHandler（控制台）
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) >= 1, "缺少 StreamHandler"
