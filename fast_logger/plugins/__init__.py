import importlib
from typing import Any

# Plugins that take only (logger,) as arguments
_SIMPLE_PLUGINS = {"fastapi", "requests", "sqlalchemy", "openai", "celery"}

# Plugins that take (target, logger) — target is the app/client/engine
_TARGET_PLUGINS = {"flask", "redis"}


def load_plugin(logger: Any, plugin_name: str, target: Any = None) -> None:
    """
    Load and activate a named plugin.

    Simple plugins (fastapi, requests, sqlalchemy, openai, celery):
        load_plugin(logger, "fastapi")

    Target plugins (flask, redis) require the app/client:
        load_plugin(logger, "flask", app)
        load_plugin(logger, "redis", redis_client)
    """
    try:
        plugin_module = importlib.import_module(
            f".{plugin_name}", package="fast_logger.plugins"
        )
        if target is not None and hasattr(plugin_module, "patch"):
            plugin_module.patch(target, logger)  # type: ignore[arg-type]
        elif hasattr(plugin_module, "patch"):
            plugin_module.patch(logger)
        else:
            logger.warning(f"Plugin '{plugin_name}' has no patch() method.")
    except ImportError as e:
        logger.warning(f"Could not load plugin '{plugin_name}': {e}")
