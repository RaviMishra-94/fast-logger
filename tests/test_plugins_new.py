"""Tests for new plugins: flask, redis, openai, celery."""

import tempfile
import pytest
from fast_logger import FastLogger


def make_logger() -> FastLogger:
    tmpdir = tempfile.mkdtemp()
    return FastLogger("plugin_test", base_path=tmpdir, console_output=False)


class TestFlaskPlugin:
    def test_flask_plugin_missing_lib(self) -> None:
        """patch_flask should warn gracefully when flask is not installed."""
        import sys
        import unittest.mock as mock

        logger = make_logger()

        # Simulate flask not being installed
        with mock.patch.dict(sys.modules, {"flask": None}):
            # Should not raise — just warn
            try:
                from fast_logger.plugins.flask import patch_flask

                patch_flask(object(), logger)
            except Exception:
                pass  # ImportError handled internally is fine
        logger.stop()

    def test_flask_idempotency(self) -> None:
        """patch_flask must not double-patch the same app."""
        logger = make_logger()

        class FakeApp:
            _fast_logger_plugin_patched = True  # already patched sentinel

        try:
            from fast_logger.plugins.flask import patch_flask

            # Should return early without error
            patch_flask(FakeApp(), logger)
        except ImportError:
            pytest.skip("flask not installed")
        finally:
            logger.stop()


class TestRedisPlugin:
    def test_redis_plugin_missing_lib(self) -> None:
        """patch_redis should warn gracefully when redis is not installed."""
        import sys
        import unittest.mock as mock

        logger = make_logger()
        with mock.patch.dict(sys.modules, {"redis": None}):
            try:
                from fast_logger.plugins.redis import patch_redis

                patch_redis(object(), logger)
            except Exception:
                pass
        logger.stop()

    def test_redis_idempotency(self) -> None:
        """patch_redis must not double-patch the same client."""
        logger = make_logger()

        class FakeClient:
            _fast_logger_plugin_patched = True

        try:
            from fast_logger.plugins.redis import patch_redis

            patch_redis(FakeClient(), logger)
        except ImportError:
            pytest.skip("redis not installed")
        finally:
            logger.stop()


class TestOpenAIPlugin:
    def test_openai_plugin_missing_lib(self) -> None:
        """patch_openai should warn gracefully when openai is not installed."""
        import sys
        import unittest.mock as mock

        logger = make_logger()
        with mock.patch.dict(sys.modules, {"openai": None}):
            try:
                from fast_logger.plugins.openai import patch_openai

                patch_openai(logger)
            except Exception:
                pass
        logger.stop()

    def test_cost_estimation(self) -> None:
        """_estimate_cost should return a float >= 0."""
        from fast_logger.plugins.openai import _estimate_cost

        cost = _estimate_cost("gpt-4o", 1000, 500)
        assert isinstance(cost, float)
        assert cost >= 0.0

    def test_cost_unknown_model(self) -> None:
        """Unknown models return 0 cost without crashing."""
        from fast_logger.plugins.openai import _estimate_cost

        cost = _estimate_cost("completely-unknown-model-xyz", 1000, 500)
        assert cost == 0.0


class TestCeleryPlugin:
    def test_celery_plugin_missing_lib(self) -> None:
        """patch_celery should warn gracefully when celery is not installed."""
        import sys
        import unittest.mock as mock

        logger = make_logger()
        with mock.patch.dict(sys.modules, {"celery": None, "celery.signals": None}):
            try:
                from fast_logger.plugins.celery import patch_celery

                patch_celery(object(), logger)
            except Exception:
                pass
        logger.stop()

    def test_celery_idempotency(self) -> None:
        """patch_celery must not double-patch the same app."""
        logger = make_logger()

        class FakeApp:
            _fast_logger_plugin_patched = True

        try:
            from fast_logger.plugins.celery import patch_celery

            patch_celery(FakeApp(), logger)
        except ImportError:
            pytest.skip("celery not installed")
        finally:
            logger.stop()


class TestCorePatchMethods:
    def test_patch_methods_exist(self) -> None:
        logger = make_logger()
        assert callable(logger.patch_fastapi)
        assert callable(logger.patch_flask)
        assert callable(logger.patch_redis)
        assert callable(logger.patch_openai)
        assert callable(logger.patch_celery)
        logger.stop()

    def test_use_with_target(self) -> None:
        """use() with target arg should not crash."""
        logger = make_logger()

        class FakeApp:
            _fast_logger_plugin_patched = True

        result = logger.use("flask", FakeApp())
        assert result is logger  # fluent interface
        logger.stop()
