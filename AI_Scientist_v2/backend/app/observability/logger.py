"""智研星枢 - 结构化日志系统"""
import atexit
import logging
import logging.handlers
import queue
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
    if getattr(root, "_zhixing_logging_ready", False):
        return  # 幂等：重复调用不叠加 handler（否则同一条日志写两遍）
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    log_dir = settings.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log"), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(FileFormatter())

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    console.setFormatter(ColorFormatter())

    # 日志 I/O 全部挪到后台线程：Windows 控制台一旦进入「快速编辑/选中」模式，
    # 写 stdout 会永久阻塞；若在主线程写，事件循环会被一并卡死（接口全超时、
    # Ctrl+C 也被控制台当成「复制」），这就是「服务假死、停不下来」的根因。
    log_queue: queue.Queue = queue.Queue(-1)
    listener = logging.handlers.QueueListener(
        log_queue, fh, console, respect_handler_level=True)
    root.addHandler(logging.handlers.QueueHandler(log_queue))
    listener.start()
    atexit.register(listener.stop)
    root._zhixing_logging_ready = True

    for name in ["uvicorn", "sqlalchemy", "httpx", "httpcore", "multipart"]:
        logging.getLogger(name).setLevel(logging.WARNING)
    root.info("📝 日志系统初始化完成")