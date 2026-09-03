"""智研星枢 - 结构化日志系统"""
import logging
import sys
import os
from datetime import datetime
from app.config import settings


class ColorFormatter(logging.Formatter):
    COLORS = {"DEBUG": "\033[36m", "INFO": "\033[32m", "WARNING": "\033[33m", "ERROR": "\033[31m", "CRITICAL": "\033[41m"}
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{color}[{ts}] [{record.levelname:>8}] {record.name}: {record.getMessage()}{self.RESET}"


class FileFormatter(logging.Formatter):
    def format(self, record):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{ts}] [{record.levelname:>8}] {record.name}: {record.getMessage()}"


def setup_logging(debug: bool = True):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    console.setFormatter(ColorFormatter())
    root.addHandler(console)
    log_dir = settings.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log"), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(FileFormatter())
    root.addHandler(fh)
    for name in ["uvicorn", "sqlalchemy", "httpx", "httpcore", "multipart"]:
        logging.getLogger(name).setLevel(logging.WARNING)
    root.info("📝 日志系统初始化完成")