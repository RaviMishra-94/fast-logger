import importlib
from typing import Any


def load_plugin(logger: Any, plugin_name: str) -> None:
    try:
        plugin_module = importlib.import_module(
            f".{plugin_name}", package="fast_logger.plugins"
        )
        if hasattr(plugin_module, "patch"):
            plugin_module.patch(logger)
        else:
            logger.warning(f"Plugin '{plugin_name}' has no patch() method.")
    except ImportError as e:
        logger.warning(f"Could not load plugin '{plugin_name}': {e}")
