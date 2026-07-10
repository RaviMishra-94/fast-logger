import time
from fast_logger import FastLogger


def main():
    # 1. Initialize Logger with Tier 1 and Tier 2 features
    print("\n" + "=" * 50)
    print("🚀 FAST LOGGER TIER 1 & 2 DEMO 🚀")
    print("=" * 50 + "\n")

    logger = FastLogger(
        name="demo_logger",
        level="DEBUG",
        color_output=True,  # Beautiful terminal output
        json_format=False,  # Set to True to see structured JSON logs instead
        async_safe=True,  # Uses non-blocking QueueHandler
    )

    # Basic logging with icons and colors
    logger.debug("Starting initialization sequence...")
    logger.info("Application successfully connected to database.")
    logger.warning("Memory usage is slightly elevated (75%).")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("Failed to process transaction: Division by zero")
    logger.critical("System shutdown imminent!")

    print("\n--- Context Logger (bind) ---")

    # 2. Context binding
    ctx_logger = logger.bind(request_id="REQ-8472", user="Alice")
    ctx_logger.info("Processing checkout payment")
    ctx_logger.debug("Validating credit card...")
    ctx_logger.info("Payment confirmed")

    print("\n--- Execution Timing (timer) ---")

    # 3. Execution timing using context manager
    with logger.timer("Heavy Database Migration"):
        time.sleep(0.3)  # Simulating heavy work
        ctx_logger.info("Migration step 1 complete")
        time.sleep(0.2)
        ctx_logger.info("Migration step 2 complete")

    print("\n--- Function Tracing (@trace) ---")

    # 4. Function tracing
    @logger.trace(level="DEBUG")
    def fetch_user_data(user_id: int):
        time.sleep(0.4)
        if user_id < 0:
            logger.warning(f"Invalid user_id {user_id} provided")
            return None
        return {"id": user_id, "name": "Bob"}

    fetch_user_data(42)
    fetch_user_data(-1)

    print("\n--- Rich Table Rendering ---")

    # 5. Table printing (requires 'rich' installed)
    users = [
        {"ID": 1, "Name": "Alice", "Role": "Admin", "Status": "Active"},
        {"ID": 2, "Name": "Bob", "Role": "Editor", "Status": "Inactive"},
        {"ID": 3, "Name": "Charlie", "Role": "Viewer", "Status": "Active"},
    ]
    logger.table(users, title="System Users")

    # Allow async queue listener to finish processing
    time.sleep(0.1)
    print("\n" + "=" * 50)
    print("Demo complete! Check out 'logs/demo_logger.log' to see the file output.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
