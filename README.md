# celery-once-task

Prevent duplicate Celery task execution using Redis locks.

When the same task is called multiple times with the same arguments, `celery-once-task` makes sure only one instance gets queued and only one instance runs at a time. It uses Redis to coordinate locks across workers.

## How It Works

The library provides two independent locks:

- **Queue lock**: acquired when `apply_async()` / `delay()` is called. If a lock already exists for that task + arguments combination, the call is silently dropped (returns `None`). Released when the worker picks up the task.
- **Running lock**: acquired when the worker starts executing the task. If another worker is already running the same task with the same arguments, the new execution is rejected. Released when the task finishes (success, failure, or revocation).

Both locks use Redis keys with a TTL, so they expire automatically if something goes wrong.

Lock keys are built from the task name and a SHA-256 hash of the arguments, so two calls with different arguments are treated as separate tasks.

## Installation

```bash
pip install celery-once-task
```

For Django integration:

```bash
pip install celery-once-task[django]
```

## Requirements

- Python 3.9+
- Celery 5.0+
- Redis 4.0+ (Python client)
- A running Redis server

## Quick Start

> **Using Django?** Skip to [Django Integration](#django-integration), it handles configuration and signals for you automatically.

### 1. Configure

Call this once at app startup, before any tasks run. Add it to your Celery app module (e.g., `celery.py` or wherever you create your `Celery()` instance).

```python
# celery.py
from celery_once_task import configure

configure(
    redis_url="redis://localhost:6379/3",
    queue_lock_timeout=3600,
    running_lock_timeout=3600,
)
```

All three settings are optional. These are the defaults.

### 2. Connect Signals

Add this right after your `configure()` call in the same file (e.g., `celery.py`).

```python
# celery.py
from celery_once_task import setup_once_task_signals

setup_once_task_signals()
```

This hooks into Celery's `task_revoked` and `task_internal_error` signals to release locks when tasks are revoked or hit internal errors.

### 3. Register the Worker Boot Step

Also in `celery.py`, after creating your Celery app instance:

```python
# celery.py
from celery_once_task import OnceTaskUnlockBootStep

app.steps["worker"].add(OnceTaskUnlockBootStep)
```

This releases running locks for any active tasks when a worker shuts down.

### 4. Use It

In your task modules (e.g., `tasks.py`):

```python
# tasks.py
from celery import shared_task
from celery_once_task import OnceTask

@shared_task(base=OnceTask)
def my_task(taskArg1, taskArg2):
    ...
```

That's it. Calling `my_task.delay(42)` multiple times will only queue one instance. If a worker is already running `my_task(42)`, a second worker won't start another one.

## Django Integration

If you use Django, the library provides an `AppConfig` that handles configuration and signal setup automatically. You only need two steps: add it to `INSTALLED_APPS` and register the boot step.

### 1. Add to `INSTALLED_APPS`

In your Django settings file (e.g., `settings.py`):

```python
# settings.py
INSTALLED_APPS = [
    ...
    "celery_once_task.django.OnceTaskAppConfig",
]
```

### 2. Set Django Settings (optional)

In the same settings file (e.g., `settings.py`):

```python
# settings.py
CELERY_ONCE_REDIS_URL = "redis://localhost:6379/3"
CELERY_ONCE_QUEUE_LOCK_TIMEOUT = 3600       # seconds, default: 3600
CELERY_ONCE_RUNNING_LOCK_TIMEOUT = 3600     # seconds, default: 3600
```

All three are optional. The defaults are shown above.

### 3. Register the Boot Step

In your Celery app module (e.g., `celery.py`):

```python
# celery.py
from celery_once_task import OnceTaskUnlockBootStep

app.steps["worker"].add(OnceTaskUnlockBootStep)
```

### 4. Use It

In your task modules (e.g., `tasks.py`):

```python
# tasks.py
from celery import shared_task
from celery_once_task import OnceTask

@shared_task(base=OnceTask)
def my_task(taskArg1, taskArg2):
    ...
```

## Configuration Reference

| Setting | Type | Default | Description |
|---|---|---|---|
| `redis_url` | `str` | `redis://localhost:6379/3` | Redis server URL for storing locks |
| `queue_lock_timeout` | `int` | `3600` | TTL in seconds for queue locks |
| `running_lock_timeout` | `int` | `3600` | TTL in seconds for running locks |

When using Django, prefix these with `CELERY_ONCE_` and set them in your Django settings (e.g., `CELERY_ONCE_REDIS_URL`).

## Per-Task Options

You can enable or disable each lock per task by passing `queue_lock` and `running_lock` directly in the decorator:

```python
from celery import shared_task
from celery_once_task import OnceTask

@shared_task(base=OnceTask, queue_lock=False, running_lock=True)
def my_task():
    ...
```

| Option | Type | Default | Description |
|---|---|---|---|
| `queue_lock` | `bool` | `True` | Enable/disable the queue lock for this task |
| `running_lock` | `bool` | `True` | Enable/disable the running lock for this task |

Examples:

```python
# Only prevent concurrent execution, allow multiple queued instances
@shared_task(base=OnceTask, queue_lock=False)
def allow_queue_duplicates():
    ...

# Only prevent duplicate queueing, allow concurrent execution
@shared_task(base=OnceTask, running_lock=False)
def allow_parallel_runs():
    ...
```

## API

#### `celery_once_task.configure(**kwargs)`

Set the global configuration. Call this once at startup before any tasks run.

#### `celery_once_task.setup_once_task_signals()`

Connect Celery signals for lock cleanup on task revocation and internal errors.

#### `celery_once_task.teardown_once_task_signals()`

Disconnect the signals. Useful in tests.

#### `celery_once_task.OnceTask`

Celery `Task` subclass. Use as `base=OnceTask` in your task decorators.

#### `celery_once_task.OnceTaskLocked`

Exception raised (subclass of `celery.exceptions.Reject`) when a task is rejected because a running lock already exists.

#### `celery_once_task.OnceTaskUnlockBootStep`

Celery worker boot step that releases running locks on shutdown.

## How Lock Keys Are Built

Lock keys follow this pattern:

```
once_task:{task_name}:{hash}:{lock_type}
```

- `task_name`: the full dotted task name (e.g., `myapp.tasks.my_task`)
- `hash`: first 16 characters of a SHA-256 hash of the serialized arguments
- `lock_type`: either `queue` or `running`

Two calls with different arguments get different lock keys and run independently.

## License

MIT
