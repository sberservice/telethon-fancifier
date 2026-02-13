from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "telethon-fancifier"
APP_AUTHOR = "telethon-fancifier"

_PORTABLE_MODE = os.environ.get("TELETHON_FANCIFIER_PORTABLE", "").lower() in ("1", "true", "yes")


def is_portable_mode() -> bool:
    """Check if portable mode is enabled via environment variable."""
    return _PORTABLE_MODE


def get_data_dir() -> Path:
    """Get data directory - either portable (./data) or platform-specific."""
    if is_portable_mode():
        return Path.cwd() / "data"
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def get_config_path() -> Path:
    """Get config file path."""
    return get_data_dir() / "config.json"


def get_log_file_path() -> Path:
    """Get log file path."""
    return get_data_dir() / "logs" / "app.log"


def get_session_dir() -> Path:
    """Get session directory for Telethon session files."""
    return get_data_dir() / "sessions"
