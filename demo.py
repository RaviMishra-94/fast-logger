import time
from fast_logger import FastLogger

def main():
    # 1. Initialize Logger
    logger = FastLogger(
        "demo_app",
        console_output=True,
        color_output=True,
        json_format=False,
    )

    print("\n" + "="*50)
    print("🌟 TIER 1: CORE LOGGING 🌟")
    print("="*50)
    logger.info("Application starting up...")
    logger.debug("Loaded configuration from env.")
    logger.warning("Memory usage is getting a bit high.")
    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.error("Failed to calculate trajectory", exc_info=e)
    logger.info("Core initialization complete! 🚀")

    print("\n" + "="*50)
    print("🌟 TIER 2: DEVELOPER PRODUCTIVITY 🌟")
    print("="*50)

    # Context Binding
    user_logger = logger.bind(user_id="U-123", req_id="REQ-999")
    user_logger.info("User logged in successfully")

    # Formatters
    logger.sql("SELECT * FROM users WHERE active = True;")
    
    data = {"server": "ubuntu-1", "status": "healthy", "uptime": 3600, "metrics": {"cpu": "45%", "mem": "1GB"}}
    logger.json(data)

    class FakeResponse:
        status_code = 200
        text = '{"message": "success"}'
        headers = {"Content-Type": "application/json"}
        class Req:
            method = "POST"
        request = Req()
        url = "https://api.example.com/login"
    logger.http(FakeResponse())

    # Tools
    print("\n--- Inspect Tool ---")
    class DatabaseConnection:
        def __init__(self):
            self.host = "localhost"
            self.port = 5432
            self.is_connected = True
    logger.inspect(DatabaseConnection())

    print("\n--- Benchmark Tool ---")
    def dummy_task():
        time.sleep(0.01)
    logger.benchmark("Data Processing", dummy_task, iterations=5)

    print("\n--- Curl Converter ---")
    logger.curl({"method": "POST", "url": "https://api.test.com/data", "headers": {"Auth": "Bearer 123"}, "json": {"key": "val"}})

    print("\n" + "="*50)
    print("🌟 TIER 3: ADVANCED DIAGNOSTICS & UI 🌟")
    print("="*50)

    print("\n--- Markdown & Tree ---")
    logger.markdown("# System Status\n- **CPU**: Good\n- **Mem**: 50%")
    logger.tree("App Structure", {"src": ["main.py", "utils.py"], "tests": ["test_core.py"]})

    print("\n--- Progress Bar ---")
    with logger.progress() as progress:
        task = progress.add_task("[green]Processing files...", total=3)
        for i in range(3):
            time.sleep(0.1)
            progress.advance(task)

    print("\n--- Request Patching (Demo) ---")
    logger.info("Monkey-patching requests library...")
    logger.patch_requests()

    print("\n--- Timeline Execution Blocks ---")
    with logger.timeline("Database Query"):
        time.sleep(0.15)
    with logger.timeline("Data Transformation"):
        time.sleep(0.05)

    print("\n" + "="*50)
    print("🎉 DEMO COMPLETE 🎉")
    print("="*50)
    print("Try the interactive tools:")
    print("  Log Viewer:  python -m fast_logger.viewer app.log")
    print("  Gantt Chart: python -m fast_logger.timeline app.log")
    print("  Log Replay:  python -m fast_logger.replay app.log")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
