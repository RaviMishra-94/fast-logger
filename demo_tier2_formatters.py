import logging
from fast_logger import get_logger
import sys


def main() -> None:
    print("=" * 50)
    print("🚀 FAST LOGGER TIER 2 FORMATTERS DEMO 🚀")
    print("=" * 50)
    print("\n")

    logger = get_logger("tier2_logger", level="DEBUG", color_output=True)

    print("--- 1. SQL Formatter ---")
    sql_query = """
    SELECT users.id, users.name, orders.total
    FROM users
    LEFT JOIN orders ON users.id = orders.user_id
    WHERE users.status = 'active'
    ORDER BY orders.created_at DESC LIMIT 10;
    """
    logger.sql(sql_query)

    print("\n--- 2. JSON Formatter ---")
    data = {
        "user_id": 42,
        "username": "alice",
        "preferences": {"theme": "dark", "notifications": ["email", "sms"]},
        "is_active": True,
    }
    logger.json(data)

    print("\n--- 3. HTTP Formatter ---")
    # Using a simple dict representing a request
    http_payload = {
        "status": 201,
        "method": "POST",
        "url": "https://api.example.com/v1/users",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer token123",
        },
        "body": '{"id": 42, "status": "created"}',
    }
    logger.http(http_payload)

    print("\n--- 4. Object Inspector ---")

    class CustomUser:
        """A simple user class."""

        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

        def get_profile(self) -> str:
            return f"{self.name}, {self.age} years old"

    user = CustomUser("Bob", 30)
    logger.inspect(user)

    print("\n--- 5. Exception Helper (Context Manager) ---")
    try:
        with logger.catch("Critical failure during payment processing!", reraise=False):

            def process_payment(amount: float) -> None:
                if amount < 0:
                    raise ValueError("Amount cannot be negative.")
                print("Processing...")

            process_payment(-50.0)
    except Exception:
        pass  # Already caught and logged by logger.catch!

    print("\n" + "=" * 50)
    print("Demo complete! All Tier 2 formatting features tested successfully.")
    print("=" * 50)


if __name__ == "__main__":
    main()
