"""
验证配置: .env 加载正确，所有关键字段存在且非空
"""


class TestConfigFromEnv:
    """验证 .env 配置是否正确加载到各子模块。"""

    def test_postgres_loaded(self):
        from app.config import config
        pg = config.postgres
        assert pg.host, "POSTGRES_HOST 为空"
        assert pg.port, "POSTGRES_PORT 为空"
        assert pg.user, "POSTGRES_USER 为空"
        assert "postgresql://" in pg.url, "PG URL 构造错误"
        assert "asyncpg" in pg.async_url, "异步 URL 缺少 asyncpg"

    def test_redis_loaded(self):
        from app.config import config
        r = config.redis
        assert r.host, "REDIS_HOST 为空"
        assert r.port, "REDIS_PORT 为空"
        assert "redis://" in r.url, "Redis URL 构造错误"

    def test_okx_loaded(self):
        from app.config import config
        o = config.okx
        if config.env != "test":
            assert o.api_key, "OKX_API_KEY 为空（模拟盘也需要）"

    def test_ai_loaded(self):
        from app.config import config
        assert config.ai.provider in ("deepseek", "qwen")
        if config.ai.provider == "deepseek":
            assert config.ai.deepseek_api_key, "DEEPSEEK_API_KEY 为空"

    def test_trade_defaults(self):
        from app.config import config
        t = config.trade
        assert t.symbol == "BTC/USDT:USDT"
        assert t.tick_interval_seconds == 180
        assert t.leverage >= 1
