"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: logger.py 日志模块
描述: 日志模块 — 同时输出到控制台（简洁格式）和轮转文件（完整格式）

包含:
- 函数: setup_logging — 配置并初始化全局 logger
- 函数: get_logger — 获取已配置的 logger 实例（懒加载）
- 常量: _logger — 全局 logger 缓存
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_logger = None  # 全局 logger 缓存


def setup_logging(
    name: str = "trading_bot",
    log_file: str = "logs/trading_bot.log",
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 单个日志文件最大 10 MB
    backup_count: int = 5,  # 保留的轮转文件数量
) -> logging.Logger:
    """配置并返回全局 logger，同时写入文件和控制台"""
    global _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # 文件 handler — 完整格式（含文件名、行号）
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 控制台 handler — 简洁格式（仅时间和级别）
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """获取已配置的 logger，若未初始化则自动使用默认参数初始化"""
    global _logger
    if _logger is None:
        setup_logging()
    return _logger


if __name__ == "__main__":
    logger = setup_logging()
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告")
    logger.error("这是错误")
    print("日志测试完成，检查 trading_bot.log 文件")
