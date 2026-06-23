"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_shutdown.py shutdown_logging 测试
描述: 验证 shutdown_logging 清理所有 handler
"""

import logging
from app.core.logger import setup_logging, shutdown_logging


def test_shutdown_logging_removes_root_handlers():
    setup_logging()
    assert len(logging.root.handlers) > 0
    shutdown_logging()
    assert len(logging.root.handlers) == 0
