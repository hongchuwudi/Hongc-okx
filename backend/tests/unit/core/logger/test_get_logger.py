"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_get_logger.py get_logger 懒加载测试
描述: 验证 get_logger 返回 Logger 实例，名称为 trading_bot
"""

import logging
from app.core.logger import setup_logging, get_logger, shutdown_logging


def test_get_logger_returns_logger_instance():
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "trading_bot"
    assert logger.level == logging.DEBUG


def test_get_logger_is_singleton():
    a = get_logger()
    b = get_logger()
    assert a is b


def test_get_logger_auto_initializes_without_setup():
    """不先调用 setup_logging 也能拿到 logger。"""
    # 重置全局状态后验证自动初始化
    import app.core.logger as log_mod
    log_mod._logger = None
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    log_mod._logger = None
