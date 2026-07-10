import logging
import unittest
from io import StringIO
from fast_logger.core import FastLogger

class DummyResponse:
    def __init__(self, status_code, text, method="GET", url="http://example.com"):
        self.status_code = status_code
        self.text = text
        self.headers = {"Content-Type": "application/json"}
        
        class DummyRequest:
            def __init__(self, method):
                self.method = method
        self.request = DummyRequest(method)
        self.url = url

class TestTier2Formatters(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = FastLogger("test_formatters", level=logging.DEBUG, console_output=False, async_safe=False)
        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.get_logger().addHandler(handler)

    def test_sql_formatter(self) -> None:
        self.logger.sql("SELECT * FROM users WHERE id = 1;")
        output = self.stream.getvalue()
        self.assertIn("SELECT * FROM users", output)

    def test_json_formatter(self) -> None:
        self.logger.json({"key": "value"})
        output = self.stream.getvalue()
        self.assertIn("value", output)

    def test_http_formatter_dict(self) -> None:
        self.logger.http({"status": 200, "message": "OK"})
        output = self.stream.getvalue()
        self.assertIn("OK", output)

    def test_http_formatter_obj(self) -> None:
        resp = DummyResponse(200, '{"success": true}')
        self.logger.http(resp)
        output = self.stream.getvalue()
        self.assertIn("HTTP 200", output)
        self.assertIn("http://example.com", output)
        self.assertIn('{"success": true}', output)

    def test_inspect(self) -> None:
        class User:
            name = "Alice"
        self.logger.inspect(User())
        output = self.stream.getvalue()
        self.assertIn("Alice", output)

    def test_catch_context_manager(self) -> None:
        try:
            with self.logger.catch(reraise=False):
                raise ValueError("Oops!")
        except ValueError:
            self.fail("Context manager should not reraise if reraise=False")
        
        output = self.stream.getvalue()
        self.assertIn("Oops", output)

if __name__ == "__main__":
    unittest.main()
