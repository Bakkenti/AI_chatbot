from datetime import datetime

def handle_time() -> str:
    return f"Current time: {datetime.now().strftime('%H:%M:%S')}"

def handle_help() -> str:
    return (
        "Available commands:\n"
        "/time - current time\n"
        "/sum x y - sum of numbers\n"
        "/readpdf <text> - extract text from PDF\n"
        "/savepdf <text> - save text to PDF\n"
        "/extract table_name - export first 10 rows to Excel\n"
        "/find keyword - find tables similar to keyword\n"
        "/help - show this help"
    )

def handle_sum(message: str) -> str:
    try:
        _, a, b = message.split()
        return f"Result: {int(a) + int(b)}"
    except Exception:
        return "Usage: /sum 2 3"
