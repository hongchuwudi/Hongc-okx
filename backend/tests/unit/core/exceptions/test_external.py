"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_external.py ExternalServiceError 测试
描述: 验证 ExternalServiceError status_code=502 + detail 信息
"""

from app.core.exceptions import ExternalServiceError


def test_external_service_error_has_status_502():
    ex = ExternalServiceError("OKX API timeout", detail={"retry": 3})
    assert ex.status_code == 502
    assert ex.detail == {"retry": 3}
