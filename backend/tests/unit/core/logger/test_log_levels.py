"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_log_levels.py 日志级别输出测试
描述: 验证各日志级别输出不崩溃
"""

from app.core.logger import setup_logging, shutdown_logging


def test_all_log_levels_output_without_crash():
    logger = setup_logging()
    logger.debug("core debug message")
    logger.info("core info message")
    logger.warning("core warning message")
    logger.error("core error message")
    logger.critical("core critical message")
    # 不抛异常即通过
