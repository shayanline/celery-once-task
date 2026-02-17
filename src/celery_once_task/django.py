from django.apps import AppConfig


class OnceTaskAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "celery_once_task"
    verbose_name = "Once Task"

    def ready(self):
        from django.conf import settings

        from .config import configure
        from .signals import setup_once_task_signals

        config_kwargs = {}
        redis_url = getattr(settings, "CELERY_ONCE_REDIS_URL", None)
        if redis_url:
            config_kwargs["redis_url"] = redis_url
        queue_timeout = getattr(
            settings, "CELERY_ONCE_QUEUE_LOCK_TIMEOUT", None
        )
        if queue_timeout is not None:
            config_kwargs["queue_lock_timeout"] = queue_timeout
        running_timeout = getattr(
            settings, "CELERY_ONCE_RUNNING_LOCK_TIMEOUT", None
        )
        if running_timeout is not None:
            config_kwargs["running_lock_timeout"] = running_timeout

        if config_kwargs:
            configure(**config_kwargs)

        setup_once_task_signals()
