"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: conftest.py services 集成测试公共夹具
描述: 本目录集成测试公共夹具占位

真实 Redis/数据库异步连接池是模块级全局单例，绑定到首个 event loop。
跨测试复用旧 loop 的连接会报 "Event loop is closed"。
统一由 backend/pytest.ini 的 asyncio_default_test_loop_scope = session
配置所有 async 测试共享 session 级 loop 解决，无需在此覆盖 event_loop。
"""
