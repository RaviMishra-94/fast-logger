"""Redis plugin for FastLogger — automatic command logging via execute_command wrapping."""

from __future__ import annotations

from typing import Any


def patch_redis(client: Any, logger: Any) -> None:
    """Wrap a Redis client's execute_command to log every command with latency."""
    try:
        import redis  # noqa: F401

        if getattr(client, "_fast_logger_plugin_patched", False):
            return

        import time

        original_execute = client.execute_command

        def patched_execute(*args: Any, **kwargs: Any) -> Any:
            cmd = " ".join(str(a) for a in args)
            start = time.perf_counter()
            try:
                result = original_execute(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.debug(f"Redis {cmd} → {elapsed:.1f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(f"Redis {cmd} FAILED ({elapsed:.1f}ms): {e}")
                raise

        client.execute_command = patched_execute
        setattr(client, "_fast_logger_plugin_patched", True)
        logger.info(
            "Plugin 'redis' active: Monkey-patched Redis client.execute_command"
        )
    except ImportError:
        logger.warning("Plugin 'redis' failed: 'redis' library not found.")
