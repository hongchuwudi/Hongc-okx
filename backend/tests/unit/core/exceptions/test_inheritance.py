"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_inheritance.py 异常继承链测试
描述: 验证所有异常都是 AppError 的子类
"""

from app.core.exceptions import (
    AppError, NotFoundError, BusinessError, ExternalServiceError, ConfigError,
)


def test_all_exceptions_inherit_from_app_error():
    ex_types = [NotFoundError, BusinessError, ExternalServiceError, ConfigError]
    for ex_type in ex_types:
        assert issubclass(ex_type, AppError), (
            f"{ex_type.__name__} 不是 AppError 的子类"
        )


def test_exceptions_are_exception_subclass():
    ex_types = [AppError, NotFoundError, BusinessError, ExternalServiceError, ConfigError]
    for ex_type in ex_types:
        assert issubclass(ex_type, Exception), (
            f"{ex_type.__name__} 不是 Exception 的子类"
        )
