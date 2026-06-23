"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_setup_file.py setup_logging 文件输出测试
描述: 验证 setup_logging 创建日志文件
"""

import logging
import os
from app.core.logger import setup_logging, shutdown_logging


def test_setup_logging_creates_log_file():
    logger = setup_logging()
    file_handlers = [h for h in logger.handlers
                     if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(file_handlers) == 1, f"期望 1 个 RotatingFileHandler, 实际 {len(file_handlers)}"
    log_path = file_handlers[0].baseFilename
    assert os.path.exists(log_path), f"日志文件不存在: {log_path}"
    assert os.path.getsize(log_path) >= 0
