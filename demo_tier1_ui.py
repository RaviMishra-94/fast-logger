import time
from fast_logger import get_logger

def main() -> None:
    logger = get_logger("demo", color_output=True, pretty_exceptions=True)
    
    logger.info("Starting Final Features Demo...")
    
    logger.markdown("# 1. Progress Bar")
    with logger.progress() as progress:
        task1 = progress.add_task("[red]Downloading...", total=100)
        task2 = progress.add_task("[green]Processing...", total=100)
        
        while not progress.finished:
            progress.update(task1, advance=2.5)
            progress.update(task2, advance=1.2)
            time.sleep(0.02)
            
    logger.markdown("# 2. Tree Printing")
    data = {
        "user_id": 123,
        "history": ["login", "purchase", "logout"],
        "metadata": {
            "ip": "127.0.0.1",
            "agent": "curl/7.68.0"
        }
    }
    logger.tree("User Session Data", data)
    
    logger.markdown("# 3. cURL Generator")
    logger.curl({
        "method": "POST",
        "url": "https://api.stripe.com/v1/charges",
        "headers": {
            "Authorization": "Bearer sk_test_123",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "body": "amount=2000&currency=usd&source=tok_mastercard"
    })
    
    logger.markdown("# 4. Benchmark Helper")
    def heavy_work(n: int) -> int:
        s = 0
        for i in range(n):
            s += i
        return s
        
    logger.benchmark("Heavy Computation (100k)", heavy_work, iterations=10, n=100_000)
    
    logger.markdown("# 5. Pretty Tracebacks (Global)")
    try:
        def deep_func() -> None:
            a = 10
            b = 0
            return a / b
        deep_func()
    except ZeroDivisionError:
        logger.exception("Oops! But look how pretty this is natively.")

if __name__ == "__main__":
    main()
