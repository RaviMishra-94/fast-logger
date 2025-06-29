#!/usr/bin/env python3
"""
Basic usage examples for fast-logger
"""

from fast_logger import quick_logger, get_logger, setup_logger


def main():
    print("=== Fast Logger Basic Examples ===\n")

    # Example 1: Super quick setup
    print("1. Quick Logger:")
    logger1 = quick_logger("quick_demo")
    logger1.info("This is the quickest way to get logging!")
    logger1.warning("Easy peasy!")

    print("\n" + "=" * 50 + "\n")

    # Example 2: Standard setup with some customization
    print("2. Standard Logger with custom level:")
    logger2 = setup_logger("standard_demo", level="DEBUG")
    logger2.debug("Debug message - you can see this!")
    logger2.info("Info message")
    logger2.error("Error message")

    print("\n" + "=" * 50 + "\n")

    # Example 3: Using FastLogger class directly
    print("3. FastLogger class with custom settings:")
    logger3 = get_logger(
        "advanced_demo",
        level="INFO",
        max_file_size_mb=10,
        backup_count=2
    )

    logger3.info("This logger has custom file size limits")
    logger3.warning("Files will rotate at 10MB")

    print("\n" + "=" * 50 + "\n")

    # Example 4: Exception logging
    print("4. Exception logging:")
    logger4 = quick_logger("exception_demo")

    try:
        result = 10 / 0
    except ZeroDivisionError:
        logger4.exception("Caught an exception!")

    print("\nCheck the 'logs' folder for all log files!")


if __name__ == "__main__":
    main()