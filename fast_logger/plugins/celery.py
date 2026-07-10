"""Celery plugin for FastLogger — logs task lifecycle via Celery signals."""

from __future__ import annotations

from typing import Any


def patch_celery(app: Any, logger: Any) -> None:
    """Connect FastLogger to Celery signals for task start/finish/failure logging."""
    try:
        from celery import signals  # type: ignore

        if getattr(app, "_fast_logger_plugin_patched", False):
            return

        import time

        _task_start_times: dict[str, float] = {}

        @signals.task_prerun.connect
        def on_task_prerun(
            task_id: str, task: Any, args: Any, kwargs: Any, **extra: Any
        ) -> None:
            _task_start_times[task_id] = time.perf_counter()
            logger.info(f"Task Started: {task.name} [{task_id}]")

        @signals.task_postrun.connect
        def on_task_postrun(
            task_id: str, task: Any, retval: Any, state: str, **extra: Any
        ) -> None:
            start = _task_start_times.pop(task_id, None)
            elapsed = (
                f"{(time.perf_counter() - start) * 1000:.1f}ms" if start else "?ms"
            )
            logger.info(
                f"Task Finished: {task.name} [{task_id}] state={state} ({elapsed})"
            )

        @signals.task_failure.connect
        def on_task_failure(
            task_id: str, exception: Exception, traceback: Any, **extra: Any
        ) -> None:
            _task_start_times.pop(task_id, None)
            logger.error(
                f"Task Failed: [{task_id}] {type(exception).__name__}: {exception}"
            )

        @signals.task_retry.connect
        def on_task_retry(request: Any, reason: Any, einfo: Any, **extra: Any) -> None:
            logger.warning(f"Task Retrying: [{request.id}] reason={reason}")

        setattr(app, "_fast_logger_plugin_patched", True)
        logger.info("Plugin 'celery' active: Connected to Celery task signals")
    except ImportError:
        logger.warning("Plugin 'celery' failed: 'celery' library not found.")
