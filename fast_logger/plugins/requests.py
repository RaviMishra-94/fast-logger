from typing import Any
import time


def patch(logger: Any) -> None:
    try:
        import requests

        if hasattr(requests.Session, "_fast_logger_plugin_patched"):
            return

        original_request = requests.Session.request

        def patched_request(self: Any, method: str, url: str, **kwargs: Any) -> Any:
            logger.debug(f"Request: {method} {url}")
            start_time = time.perf_counter()
            response = original_request(self, method, url, **kwargs)
            elapsed = (time.perf_counter() - start_time) * 1000

            logger.http(response, level="DEBUG")
            logger.debug(f"Response: {response.status_code} (took {elapsed:.2f}ms)")
            return response

        requests.Session.request = patched_request  # type: ignore
        setattr(requests.Session, "_fast_logger_plugin_patched", True)
        logger.info("Plugin 'requests' active: Monkey-patched requests.Session.request")
    except ImportError:
        logger.warning("Plugin 'requests' failed: 'requests' library not found.")
