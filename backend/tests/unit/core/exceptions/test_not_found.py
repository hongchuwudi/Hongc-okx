"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_not_found.py NotFoundError 测试
描述: 验证 NotFoundError status_code=404
"""

from app.core.exceptions import NotFoundError


def test_not_found_error_has_status_404():
    ex = NotFoundError("agent not found")
    assert ex.status_code == 404
    assert ex.message == "agent not found"
