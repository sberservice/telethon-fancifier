from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from telethon_fancifier.config.paths import get_log_file_path


class _ConsoleNoTracebackFormatter(logging.Formatter):
    """Форматтер консоли без вывода stack trace."""

    def formatException(self, ei: object) -> str:
        return ""


def configure_logging() -> str:
    log_path = get_log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if root.handlers:
        return str(log_path)

    console_formatter = _ConsoleNoTracebackFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(console_formatter)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    root.addHandler(stream_handler)
    root.addHandler(file_handler)
    return str(log_path)
