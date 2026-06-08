"""
创建时间: 2026-06-08
作者: hongchuwudi
文件名: exceptions.py 异常定义
描述: 统一异常层级，全局异常处理器自动转换为 HTTP 响应

包含:
- 类: AppError — 应用基础异常（status_code + message）
- 类: NotFoundError — 资源不存在 → 404
- 类: BusinessError — 业务逻辑错误 → 400
- 类: ExternalServiceError — 外部服务异常（OKX/Redis/DeepSeek）→ 502
- 类: ConfigError — 配置错误 → 500
- 函数: _handoff_detect — 传输信号的检测函数（HANDOFF_SIGNAL / ASK_SIGNAL）
"""


# 应用基础异常 — 所有业务异常的父类
class AppError(Exception):
    status_code: int = 500

    def __init__(self, message: str, detail: dict | None = None):
        self.message = message
        self.detail = detail or {}


# 资源不存在 — HTTP 404
class NotFoundError(AppError):
    status_code = 404


# 业务逻辑错误 — HTTP 400
class BusinessError(AppError):
    status_code = 400


# 外部服务异常 — HTTP 502（OKX / Redis / DeepSeek 调用失败）
class ExternalServiceError(AppError):
    status_code = 502


# 配置错误 — HTTP 500
class ConfigError(AppError):
    status_code = 500
