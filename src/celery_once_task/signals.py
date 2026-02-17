from celery.signals import task_internal_error, task_revoked

from .utils import generate_lock_key, release_lock


def _on_task_revoked(sender=None, request=None, **kwargs):
    if not request:
        return
    task_id = getattr(request, "id", None)
    task_name = getattr(request, "task", None)
    if not task_name or not task_id:
        return
    args = getattr(request, "args", ())
    kwargs_dict = getattr(request, "kwargs", {})

    queue_key = generate_lock_key(task_name, args, kwargs_dict, "queue")
    running_key = generate_lock_key(task_name, args, kwargs_dict, "running")

    release_lock(running_key, task_id)
    release_lock(queue_key, task_id)


def _on_task_internal_error(
    sender=None, task_id=None, args=None, kwargs=None, **other
):
    if not sender or not task_id:
        return
    task_name = getattr(sender, "name", None)
    if not task_name:
        return
    queue_key = generate_lock_key(task_name, args, kwargs, "queue")
    running_key = generate_lock_key(task_name, args, kwargs, "running")
    release_lock(running_key, task_id)
    release_lock(queue_key, task_id)


def setup_once_task_signals():
    task_revoked.connect(_on_task_revoked)
    task_internal_error.connect(_on_task_internal_error)


def teardown_once_task_signals():
    task_revoked.disconnect(_on_task_revoked)
    task_internal_error.disconnect(_on_task_internal_error)
