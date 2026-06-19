"""
日志模块 — 同时输出到控制台和轮转文件
"""
import logging
import sys
from logging.handlers import RotatingFileHandler

_logger = None


def setup_logging(
    name: str = "trading_bot",
    log_file: str = "trading_bot.log",
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """配置并返回全局 logger"""
    global _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # 文件 handler — 完整格式
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

    # 控制台 handler — 简洁格式
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
    """获取已配置的 logger，若未初始化则自动初始化"""
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
