from typing import Any
import time


def patch(logger: Any) -> None:
    try:
        from sqlalchemy import event  # type: ignore
        from sqlalchemy.engine import Engine  # type: ignore

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            conn.info.setdefault("query_start_time", []).append(time.perf_counter())
            logger.sql(statement, level="DEBUG")

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            start_time = conn.info["query_start_time"].pop(-1)
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Query executed in {elapsed:.2f}ms")

        logger.info(
            "Plugin 'sqlalchemy' active: Attached to sqlalchemy.engine.Engine events"
        )
    except ImportError:
        logger.warning("Plugin 'sqlalchemy' failed: 'sqlalchemy' library not found.")
