import logging
import time
from fast_logger import get_logger


def main() -> None:
    print("=" * 50)
    print("🚀 FAST LOGGER TIER 3 DEMO 🚀")
    print("=" * 50)
    print("\n")

    # 1. Initialize Logger with mask_secrets=True
    logger = get_logger(
        "tier3_logger",
        level="DEBUG",
        color_output=True,
        mask_secrets=True,
    )

    print("--- Secret Masking ---")
    logger.info("Connecting to database with password='SuperSecretPassword123'")
    logger.debug("API token received: bearer 1234567890abcdef")

    print("\n--- Variable Watcher ---")
    user_data = {"id": 42, "name": "Alice"}
    logger.watch("user_data", user_data)

    print("\n--- Change Detector (Diff) ---")
    new_user_data = {"id": 42, "name": "Alice", "role": "admin"}
    logger.diff(user_data, new_user_data)

    print("\n--- AI-Style Panels ---")
    logger.panel(
        "This is an AI-generated summary of the recent logs.\n"
        "• 1 Database connection attempt\n"
        "• 1 API token received\n"
        "• 1 User role upgrade",
        title="AI Insights",
        level="INFO",
    )

    print("\n--- System & Environment Summary ---")
    logger.sysinfo()

    print("\n" + "=" * 50)
    print("Demo complete! All Tier 3 features tested successfully.")
    print("=" * 50)


if __name__ == "__main__":
    main()
