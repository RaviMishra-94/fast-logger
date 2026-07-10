"""OpenAI plugin for FastLogger — logs model, tokens, latency, and cost estimates."""

from __future__ import annotations

from typing import Any

# Static cost table (USD per 1M tokens) — update as OpenAI revises pricing
_COST_TABLE: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost given model and token counts."""
    # Fuzzy match: strip date suffixes like -2024-09-01
    key = model
    for known in _COST_TABLE:
        if model.startswith(known):
            key = known
            break
    rates = _COST_TABLE.get(key, {"input": 0.0, "output": 0.0})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


def patch_openai(logger: Any) -> None:
    """Monkey-patch openai to log model, tokens, latency, and cost for every completion."""
    try:
        import openai

        if getattr(openai, "_fast_logger_plugin_patched", False):
            return

        import time

        # Patch chat completions (v1+ API)
        try:
            original_create = openai.chat.completions.create

            def patched_chat_create(*args: Any, **kwargs: Any) -> Any:
                model = kwargs.get("model", "unknown")
                start = time.perf_counter()
                try:
                    response = original_create(*args, **kwargs)
                    elapsed = (time.perf_counter() - start) * 1000
                    usage = getattr(response, "usage", None)
                    if usage:
                        input_tok = usage.prompt_tokens
                        output_tok = usage.completion_tokens
                        cost = _estimate_cost(model, input_tok, output_tok)
                        logger.info(
                            f"OpenAI {model} | "
                            f"in={input_tok} out={output_tok} tokens | "
                            f"${cost:.6f} | {elapsed:.0f}ms"
                        )
                    else:
                        logger.info(f"OpenAI {model} | {elapsed:.0f}ms")
                    return response
                except Exception as e:
                    elapsed = (time.perf_counter() - start) * 1000
                    logger.error(f"OpenAI {model} FAILED ({elapsed:.0f}ms): {e}")
                    raise

            openai.chat.completions.create = patched_chat_create  # type: ignore
        except AttributeError:
            pass  # older openai SDK

        setattr(openai, "_fast_logger_plugin_patched", True)
        logger.info(
            "Plugin 'openai' active: Monkey-patched openai.chat.completions.create"
        )
    except ImportError:
        logger.warning("Plugin 'openai' failed: 'openai' library not found.")
