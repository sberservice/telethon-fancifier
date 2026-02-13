from __future__ import annotations

import os
from dataclasses import dataclass

from telethon_fancifier.core.errors import AppError


@dataclass(slots=True)
class TelegramCredentials:
    api_id: int
    api_hash: str
    session_name: str


def read_telegram_credentials() -> TelegramCredentials:
    raw_api_id = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    session_name = os.getenv("TELEGRAM_SESSION_NAME", "telethon_fancifier").strip()

    if not raw_api_id or not api_hash:
        raise AppError(
            "Не заданы TELEGRAM_API_ID/TELEGRAM_API_HASH. "
            "Создайте .env из .env.example и заполните значения."
        )

    try:
        api_id = int(raw_api_id)
    except ValueError as exc:
        raise AppError("TELEGRAM_API_ID должен быть целым числом.") from exc

    if api_id <= 0:
        raise AppError("TELEGRAM_API_ID должен быть положительным числом.")

    return TelegramCredentials(api_id=api_id, api_hash=api_hash, session_name=session_name)
