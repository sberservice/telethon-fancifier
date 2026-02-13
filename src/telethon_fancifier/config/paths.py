from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "telethon-fancifier"
APP_AUTHOR = "telethon-fancifier"


def get_data_dir() -> Path:
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def get_config_path() -> Path:
    return get_data_dir() / "config.json"


def get_log_file_path() -> Path:
    return get_data_dir() / "logs" / "app.log"
