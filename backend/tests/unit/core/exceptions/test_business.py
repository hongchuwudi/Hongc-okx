"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_business.py BusinessError 测试
描述: 验证 BusinessError status_code=400
"""

from app.core.exceptions import BusinessError


def test_business_error_has_status_400():
    ex = BusinessError("signal not found")
    assert ex.status_code == 400
    assert "signal" in ex.message
