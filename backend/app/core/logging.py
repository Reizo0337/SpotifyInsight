import time

class Logger:
    @staticmethod
    def info(tag, message):
        print(f"[{tag}] {message}")

    @staticmethod
    def error(tag, message):
        print(f"[{tag}] ERROR: {message}")

    @staticmethod
    def warning(tag, message):
        print(f"[{tag}] WARNING: {message}")

    @staticmethod
    def success(tag, message):
        print(f"[{tag}] SUCCESS: {message}")

    @staticmethod
    def time(tag, message, start_time):
        elapsed = time.time() - start_time
        print(f"[{tag}] {message} ({elapsed:.3f}s)")
