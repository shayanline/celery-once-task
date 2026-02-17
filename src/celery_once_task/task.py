import logging
from typing import Any

from celery import Task, states
from celery.exceptions import Reject
from celery.signals import task_failure
from kombu.utils.uuid import uuid

from .config import get_config
from .utils import generate_lock_key, release_lock

logger = logging.getLogger(__name__)


class OnceTaskLocked(Reject):
    pass


class OnceTask(Task):
    queue_lock = True
    running_lock = True

    def _acquire_lock(self, key: str, task_id: str, timeout: int) -> bool:
        try:
            from .utils import get_redis

            result = get_redis().set(key, task_id, nx=True, ex=timeout)
            return bool(result)
        except Exception:
            return False

    def _release_lock(self, key: str, task_id: str) -> bool:
        return release_lock(key, task_id)

    @property
    def queue_lock_timeout(self) -> int:
        return get_config().queue_lock_timeout

    @property
    def running_lock_timeout(self) -> int:
        return get_config().running_lock_timeout

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        if self.queue_lock and not self.acks_late:
            queue_key = generate_lock_key(self.name, args, kwargs, "queue")
            self._release_lock(queue_key, task_id)

        if self.running_lock:
            running_key = generate_lock_key(self.name, args, kwargs, "running")
            if not self._acquire_lock(
                running_key, task_id, self.running_lock_timeout
            ):
                msg = f"Task {self.name} is already running with the same arguments"
                exc = OnceTaskLocked(msg)
                if not self.ignore_result:
                    self.update_state(
                        task_id=task_id,
                        state=states.REJECTED,
                        meta={"reason": msg, "result": str(exc)},
                    )
                task_failure.send(
                    sender=self,
                    task_id=task_id,
                    exception=exc,
                    args=args,
                    kwargs=kwargs,
                )
                raise exc

    def after_return(self, status, retval, task_id, args, kwargs, einfo) -> None:
        if self.queue_lock and self.acks_late:
            queue_key = generate_lock_key(self.name, args, kwargs, "queue")
            self._release_lock(queue_key, task_id)
        if self.running_lock:
            running_key = generate_lock_key(self.name, args, kwargs, "running")
            self._release_lock(running_key, task_id)

    def apply_async(self, args=None, kwargs=None, **options) -> Any:
        if self.queue_lock:
            queue_key = generate_lock_key(
                self.name, args, kwargs or {}, "queue"
            )
            task_id = options.get("task_id") or uuid()
            options["task_id"] = task_id
            if not self._acquire_lock(
                queue_key, task_id, self.queue_lock_timeout
            ):
                return None
            try:
                return super().apply_async(args, kwargs, **options)
            except Exception:
                self._release_lock(queue_key, task_id)
                raise
        return super().apply_async(args, kwargs, **options)

    def delay(self, *args, **kwargs) -> Any:
        return self.apply_async(args, kwargs)
