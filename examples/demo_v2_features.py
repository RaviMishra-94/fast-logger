import time
from fast_logger import FastLogger

def run_demo():
    print("=" * 60)
    print("🚀 FAST-LOGGER v0.2.0 FEATURES DEMO")
    print("=" * 60)
    print()

    # ---------------------------------------------------------
    # 1. Colored Output
    # ---------------------------------------------------------
    print("1️⃣ Testing Colored Console Output (color_output=True)")
    print("-" * 60)
    logger_color = FastLogger(
        name="demo_color",
        level="DEBUG",
        color_output=True,
        console_output=True
    )
    
    logger_color.debug("This is a DEBUG message (should be cyan)")
    logger_color.info("This is an INFO message (should be green)")
    logger_color.warning("This is a WARNING message (should be yellow)")
    logger_color.error("This is an ERROR message (should be red)")
    logger_color.critical("This is a CRITICAL message (should be magenta)")
    print()

    # ---------------------------------------------------------
    # 2. JSON Format Output
    # ---------------------------------------------------------
    print("2️⃣ Testing JSON Structured Output (json_format=True)")
    print("-" * 60)
    logger_json = FastLogger(
        name="demo_json",
        level="INFO",
        json_format=True,
        console_output=True
    )
    
    logger_json.info("This is a structured JSON log message")
    logger_json.error("JSON logs also handle exceptions perfectly!")
    
    try:
        1 / 0
    except ZeroDivisionError:
        logger_json.exception("Something went terribly wrong here")
    print()

    # ---------------------------------------------------------
    # 3. Async-Safe Logging
    # ---------------------------------------------------------
    print("3️⃣ Testing Async-Safe Queue Logging (async_safe=True)")
    print("-" * 60)
    
    # Using context manager for clean shutdown of the background thread
    with FastLogger(
        name="demo_async",
        level="INFO",
        color_output=True,  # Combine features!
        async_safe=True,
        console_output=True
    ) as logger_async:
        logger_async.info("This message was processed via a background QueueListener thread!")
        logger_async.info("It does not block your main event loop or thread for file/network I/O.")
        logger_async.warning("Combining async_safe=True with color_output=True works perfectly.")
        
        # Wait a tiny bit to ensure the queue processes before the script exits
        time.sleep(0.1)

    print()
    print("✅ All features demonstrated! Check the 'logs/' folder to see the generated log files.")

if __name__ == "__main__":
    run_demo()
