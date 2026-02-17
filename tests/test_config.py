from celery_once_task.config import configure, get_config, reset_config


class TestConfig:
    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    def test_default_config(self):
        config = get_config()
        assert config.redis_url == "redis://localhost:6379/3"
        assert config.queue_lock_timeout == 3600
        assert config.running_lock_timeout == 3600

    def test_configure_overrides(self):
        configure(
            redis_url="redis://custom:6379/0",
            queue_lock_timeout=120,
            running_lock_timeout=300,
        )
        config = get_config()
        assert config.redis_url == "redis://custom:6379/0"
        assert config.queue_lock_timeout == 120
        assert config.running_lock_timeout == 300

    def test_configure_partial(self):
        configure(redis_url="redis://partial:6379/1")
        config = get_config()
        assert config.redis_url == "redis://partial:6379/1"
        assert config.queue_lock_timeout == 3600

    def test_reset_config(self):
        configure(redis_url="redis://temp:6379/0")
        reset_config()
        config = get_config()
        assert config.redis_url == "redis://localhost:6379/3"
