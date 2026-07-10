import os
import platform
import sys


from typing import Any


def get_system_info() -> dict[str, Any]:
    """Returns a dictionary containing basic system and environment information."""

    info: dict[str, Any] = {
        "os": platform.system(),
        "os_release": platform.release(),
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
    }

    # Try to detect container environments
    in_docker = os.path.exists("/.dockerenv")

    # Check for Kubernetes
    in_k8s = "KUBERNETES_SERVICE_HOST" in os.environ

    info["in_container"] = in_docker or in_k8s
    info["orchestrator"] = (
        "Kubernetes" if in_k8s else ("Docker" if in_docker else "None")
    )

    # Try memory/cpu if psutil is available
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        info["cpu_percent"] = psutil.cpu_percent(interval=None)
        info["memory_used_mb"] = vm.used / (1024 * 1024)
        info["memory_total_mb"] = vm.total / (1024 * 1024)
        info["memory_percent"] = vm.percent
    except ImportError:
        pass

    return info
