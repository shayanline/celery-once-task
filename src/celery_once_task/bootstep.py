from celery import bootsteps
from celery.worker import WorkController

from .task import OnceTask
from .utils import generate_lock_key, release_lock


class OnceTaskUnlockBootStep(bootsteps.StartStopStep):
    def close(self, worker: WorkController):
        for request in worker.state.active_requests:
            if isinstance(request.task, OnceTask):
                running_key = generate_lock_key(
                    request.task_name,
                    request.args,
                    request.kwargs,
                    "running",
                )
                release_lock(running_key, request.task_id)
