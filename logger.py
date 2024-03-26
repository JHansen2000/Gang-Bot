from datetime import datetime

class Logger:
    prefix = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def info(self, message: str) -> None:
        print(f"{self.prefix} [INF] - {message}")
        return

    def warning(self, message: str) -> None:
        print(f"{self.prefix} [WRN] - {message}")
        return

    def error(self, message: str) -> None:
        print(f"{self.prefix} [ERR] - {message}")
        return

    def fatal(self, message: str) -> None:
        print(f"{self.prefix} [FAT] - {message}")
        return