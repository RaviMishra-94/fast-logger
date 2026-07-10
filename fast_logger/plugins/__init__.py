import importlib
from typing import Any

# Map plugin_name -> (function_name, needs_target)
_PLUGIN_REGISTRY: dict[str, tuple[str, bool]] = {
    # Legacy plugins — have a `patch(logger)` function
    "fastapi": ("patch", False),
    "requests": ("patch", False),
    "sqlalchemy": ("patch", False),
    # New plugins — named differently, some need a target
    "flask": ("patch_flask", True),
    "redis": ("patch_redis", True),
    "openai": ("patch_openai", False),
    "celery": ("patch_celery", True),
}


def load_plugin(logger: Any, plugin_name: str, target: Any = None) -> None:
    """
    Load and activate a named plugin.

    Simple plugins (no target needed)::

        load_plugin(logger, "fastapi")
        load_plugin(logger, "requests")
        load_plugin(logger, "sqlalchemy")
        load_plugin(logger, "openai")

    Target plugins (pass the app/client/engine)::

        load_plugin(logger, "flask", flask_app)
        load_plugin(logger, "redis", redis_client)
        load_plugin(logger, "celery", celery_app)
    """
    try:
        plugin_module = importlib.import_module(
            f".{plugin_name}", package="fast_logger.plugins"
        )

        entry = _PLUGIN_REGISTRY.get(plugin_name)
        if entry:
            func_name, needs_target = entry
            func = getattr(plugin_module, func_name, None)
            if func is None:
                logger.warning(
                    f"Plugin '{plugin_name}' has no '{func_name}()' function."
                )
                return
            if needs_target:
                if target is None:
                    logger.warning(
                        f"Plugin '{plugin_name}' requires a target object "
                        f"(e.g. logger.use('{plugin_name}', app)). Skipping."
                    )
                    return
                func(target, logger)
            else:
                func(logger)
        elif hasattr(plugin_module, "patch"):
            # Unknown plugin with a generic patch() function
            if target is not None:
                plugin_module.patch(target, logger)  # type: ignore[arg-type]
            else:
                plugin_module.patch(logger)
        else:
            logger.warning(f"Plugin '{plugin_name}' has no patch() method.")
    except ImportError as e:
        logger.warning(f"Could not load plugin '{plugin_name}': {e}")
