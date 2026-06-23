"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_base.py AppError 基础测试
描述: 验证 AppError 基类 message + status_code 默认值
"""

from app.core.exceptions import AppError


def test_app_error_has_default_status_code_500():
    ex = AppError("something broke")
    assert ex.message == "something broke"
    assert ex.status_code == 500
    assert ex.detail == {}
