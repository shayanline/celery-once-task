import hashlib
from typing import Any, Dict, Optional, Tuple, Union

import redis

from .config import get_config

_redis_client = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            get_config().redis_url, decode_responses=True
        )
    return _redis_client


def reset_redis() -> None:
    global _redis_client
    _redis_client = None


def generate_lock_key(
    task_name: str,
    args: Optional[Union[Tuple[Any, ...], list]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    lock_type: str = "",
) -> str:
    args = tuple(args) if args else ()
    kwargs = kwargs or {}
    args_str = str(args) if args else ""
    kwargs_str = str(sorted(kwargs.items())) if kwargs else ""
    combined = f"{task_name}:{args_str}:{kwargs_str}"
    key_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]
    base_key = f"once_task:{task_name}:{key_hash}"
    return f"{base_key}:{lock_type}" if lock_type else base_key


def release_lock(key: str, task_id: str) -> bool:
    try:
        redis_client = get_redis()
        value = redis_client.get(key)
        if value == task_id:
            return bool(redis_client.delete(key))
        return False
    except Exception:
        return False


def lock_exists(key: str) -> bool:
    try:
        return bool(get_redis().exists(key))
    except Exception:
        return False
