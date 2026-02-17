from dataclasses import dataclass
from typing import Optional


@dataclass
class OnceTaskConfig:
    redis_url: str = "redis://localhost:6379/3"
    queue_lock_timeout: int = 3600
    running_lock_timeout: int = 3600


_config: Optional[OnceTaskConfig] = None


def configure(**kwargs) -> OnceTaskConfig:
    global _config
    _config = OnceTaskConfig(**kwargs)
    return _config


def get_config() -> OnceTaskConfig:
    global _config
    if _config is None:
        _config = OnceTaskConfig()
    return _config


def reset_config() -> None:
    global _config
    _config = None
