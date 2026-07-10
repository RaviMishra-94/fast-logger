import io
import unittest
import time
from fast_logger import FastLogger

class TestFinalSprint(unittest.TestCase):
    def setUp(self) -> None:
        self.stream = io.StringIO()
        self.logger = FastLogger("test_final", console_output=True, color_output=False, json_format=False, compress_backups=True)
        # Override handler stream
        for h in self.logger._logger.handlers:
            if hasattr(h, "stream"):
                h.stream = self.stream

    def test_progress(self) -> None:
        with self.logger.progress() as p:
            task = p.add_task("Test", total=10)
            p.update(task, advance=10)
            
    def test_tree(self) -> None:
        data = {"a": 1, "b": {"c": [1, 2]}}
        self.logger.tree("My Tree", data)
        self.assertIn("My Tree", self.stream.getvalue())

    def test_markdown(self) -> None:
        self.logger.markdown("# Header")
        self.assertIn("Header", self.stream.getvalue())

    def test_benchmark(self) -> None:
        def dummy_work(x: int) -> int:
            return x * 2
            
        result = self.logger.benchmark("dummy", dummy_work, iterations=2, x=5)
        self.assertEqual(result, 10)
        self.assertIn("Benchmark 'dummy'", self.stream.getvalue())
        
    def test_curl(self) -> None:
        req = {
            "method": "POST",
            "url": "http://test.com",
            "headers": {"A": "B"},
            "body": {"foo": "bar"}
        }
        self.logger.curl(req)
        output = self.stream.getvalue()
        self.assertIn("curl -X POST", output)
        self.assertIn("-H 'A: B'", output)
        self.assertIn("http://test.com", output)

if __name__ == "__main__":
    unittest.main()
