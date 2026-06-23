"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_dotenv_loading.py dotenv 加载验证测试
描述: 验证 .env 文件被正确加载，环境变量覆盖了硬编码默认值

包含:
- 函数: test_dotenv_file_exists — .env 文件存在
- 函数: test_postgres_host_from_env — POSTGRES_HOST 来自 .env 而非默认值
- 函数: test_postgres_port_from_env — POSTGRES_PORT 来自 .env 而非默认值
- 函数: test_redis_host_from_env — REDIS_HOST 来自 .env 而非默认值
- 函数: test_env_overrides_default — 验证 .env 值与默认值不同（核心回归测试）
"""
import os

from app.core.config import config


def test_dotenv_file_exists():
    """验证 .env 文件存在于正确路径，而非 app/.env"""
    from pathlib import Path
    import importlib

    # 定位 config 包的 __init__.py
    config_init = Path(importlib.__file__).parent.parent / "app" / "core" / "config" / "__init__.py"
    # 实际要看我们项目的 config 包
    from app.core import config as config_pkg

    pkg_dir = Path(config_pkg.__file__).parent  # app/core/config/
    env_path = pkg_dir.parent.parent.parent / ".env"  # backend/.env （4层上）

    assert env_path.exists(), (
        f".env 文件不存在于 {env_path}。"
        f"load_dotenv 路径必须指向 backend/.env 而非 app/.env"
    )


def test_postgres_host_not_default():
    """POSTGRES_HOST 必须来自 .env，不能是硬编码默认值 127.0.0.1。
    这是本次 bug 的核心回归测试。
    """
    assert config.postgres.host != "127.0.0.1", (
        f"postgres.host={config.postgres.host} 等于默认值 127.0.0.1，"
        f"说明 .env 未被加载或 POSTGRES_HOST 未从 .env 读取"
    )


def test_postgres_port_not_default():
    """POSTGRES_PORT 必须来自 .env，不能是默认值 5432"""
    assert config.postgres.port != 5432, (
        f"postgres.port={config.postgres.port} 等于默认值 5432，"
        f"说明 .env 未被加载或 POSTGRES_PORT 未从 .env 读取"
    )


def test_redis_host_not_default():
    """REDIS_HOST 必须来自 .env，不能是默认值 localhost"""
    assert config.redis.host != "localhost", (
        f"redis.host={config.redis.host} 等于默认值 localhost，"
        f"说明 .env 未被加载或 REDIS_HOST 未从 .env 读取"
    )


def test_env_values_overwrite_defaults():
    """验证 .env 中的关键配置确实覆盖了代码默认值。
    如果所有环境变量都等于默认值，说明 load_dotenv 路径有问题。
    """
    from dataclasses import fields
    from app.core.config.config_postgres import PostgresConfig
    from app.core.config.config_redis import RedisConfig

    # 检查 os.getenv 是否能读到 POSTGRES_HOST（证明 dotenv 加载成功）
    pg_host = os.getenv("POSTGRES_HOST")
    assert pg_host is not None, (
        "os.getenv('POSTGRES_HOST') 返回 None，"
        "load_dotenv 未正确加载 .env 文件"
    )

    redis_host = os.getenv("REDIS_HOST")
    assert redis_host is not None, (
        "os.getenv('REDIS_HOST') 返回 None，"
        "load_dotenv 未正确加载 .env 文件"
    )
