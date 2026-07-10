import logging
import unittest
from io import StringIO
import json

from fast_logger.core import FastLogger
from fast_logger.masking import mask_secrets_in_string, mask_dict


class TestTier3Features(unittest.TestCase):
    def test_mask_secrets_in_string(self) -> None:
        text = "Here is my AWS key: AKIAIOSFODNN7EXAMPLE and secret: aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"
        masked = mask_secrets_in_string(text)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", masked)
        self.assertIn("********", masked)
        self.assertNotIn("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", masked)

    def test_mask_dict(self) -> None:
        data = {
            "user": "Alice",
            "password": "super_secret_password",
            "metadata": {
                "token": "1234567890",
                "apikey": "abcdef",
                "public_info": "hello",
            },
        }
        masked = mask_dict(data)
        self.assertEqual(masked["user"], "Alice")
        self.assertEqual(masked["password"], "********")
        self.assertEqual(masked["metadata"]["token"], "********")
        self.assertEqual(masked["metadata"]["apikey"], "********")
        self.assertEqual(masked["metadata"]["public_info"], "hello")

    def test_logger_masking(self) -> None:
        logger = FastLogger(
            "test_masking",
            level=logging.DEBUG,
            mask_secrets=True,
            console_output=False,
            async_safe=False,
        )
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.get_logger().addHandler(handler)

        logger.info("My password is password='secret123'")
        output = stream.getvalue()
        self.assertNotIn("secret123", output)
        self.assertIn("********", output)

    def test_watch_and_sysinfo(self) -> None:
        # Just ensure they run without error and format correctly
        logger = FastLogger(
            "test_watch", level=logging.DEBUG, console_output=False, async_safe=False
        )
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.get_logger().addHandler(handler)

        logger.watch("my_var", 42)
        logger.sysinfo()
        logger.diff({"a": 1}, {"a": 2})
        logger.panel("Hello World", title="Test Panel")

        output = stream.getvalue()
        self.assertIn("my_var", output)
        self.assertIn("System Info", output)
        self.assertIn("Test Panel", output)


if __name__ == "__main__":
    unittest.main()
