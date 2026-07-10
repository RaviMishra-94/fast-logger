import logging
from typing import Dict, Any


class BaseTheme:
    colors: Dict[int, str] = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    icons: Dict[int, str] = {
        logging.DEBUG: "🚀",
        logging.INFO: "✓",
        logging.WARNING: "⚠",
        logging.ERROR: "✗",
        logging.CRITICAL: "🔥",
    }

    rich_styles: Dict[str, str] = {
        "info": "green",
        "warning": "yellow",
        "error": "bold red",
        "critical": "bold magenta",
        "debug": "cyan",
        "key": "bold cyan",
        "value": "yellow",
    }


class CyberpunkTheme(BaseTheme):
    colors = {
        logging.DEBUG: "\033[38;5;51m",  # Neon Blue
        logging.INFO: "\033[38;5;39m",  # Bright Blue
        logging.WARNING: "\033[38;5;226m",  # Neon Yellow
        logging.ERROR: "\033[38;5;196m",  # Neon Red
        logging.CRITICAL: "\033[38;5;201m",  # Neon Pink
    }
    icons = {
        logging.DEBUG: "⚡",
        logging.INFO: "👾",
        logging.WARNING: "⚠",
        logging.ERROR: "💥",
        logging.CRITICAL: "💀",
    }
    rich_styles = {
        "info": "bright_blue",
        "warning": "bright_yellow",
        "error": "bright_red",
        "critical": "bold color(201)",
        "debug": "color(51)",
        "key": "color(201)",
        "value": "color(51)",
    }


class DraculaTheme(BaseTheme):
    colors = {
        logging.DEBUG: "\033[38;5;141m",  # Purple
        logging.INFO: "\033[38;5;84m",  # Green
        logging.WARNING: "\033[38;5;215m",  # Orange
        logging.ERROR: "\033[38;5;203m",  # Red
        logging.CRITICAL: "\033[38;5;212m",  # Pink
    }
    icons = {
        logging.DEBUG: "🦇",
        logging.INFO: "✓",
        logging.WARNING: "⚠",
        logging.ERROR: "✗",
        logging.CRITICAL: "🧛",
    }
    rich_styles = {
        "info": "color(84)",
        "warning": "color(215)",
        "error": "color(203)",
        "critical": "bold color(212)",
        "debug": "color(141)",
        "key": "bold color(141)",
        "value": "color(84)",
    }


class MinimalTheme(BaseTheme):
    colors = {
        logging.DEBUG: "\033[37m",  # White/Gray
        logging.INFO: "\033[37m",
        logging.WARNING: "\033[37m",
        logging.ERROR: "\033[37m",
        logging.CRITICAL: "\033[37m",
    }
    icons = {
        logging.DEBUG: "[D]",
        logging.INFO: "[I]",
        logging.WARNING: "[W]",
        logging.ERROR: "[E]",
        logging.CRITICAL: "[C]",
    }
    rich_styles = {
        "info": "white",
        "warning": "white",
        "error": "bold white",
        "critical": "bold white",
        "debug": "white",
        "key": "bold white",
        "value": "white",
    }


THEMES = {
    "default": BaseTheme(),
    "cyberpunk": CyberpunkTheme(),
    "dracula": DraculaTheme(),
    "minimal": MinimalTheme(),
}


def get_theme(theme_name: str) -> BaseTheme:
    if not theme_name:
        return THEMES["default"]
    return THEMES.get(theme_name.lower(), THEMES["default"])
