from __future__ import annotations

import json
from dataclasses import asdict
from json import JSONDecodeError
import logging

from telethon_fancifier.config.paths import get_config_path
from telethon_fancifier.config.schema import AppConfig, ChatConfig
from telethon_fancifier.core.errors import AppError

logger = logging.getLogger(__name__)


class ConfigStore:
    def __init__(self) -> None:
        self._path = get_config_path()

    def load(self) -> AppConfig:
        if not self._path.exists():
            return AppConfig()
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            chats = [ChatConfig(**item) for item in payload.get("chats", [])]
            return AppConfig(
                schema_version=payload.get("schema_version", 1),
                parse_mode=payload.get("parse_mode", "markdown_v2"),
                default_dry_run=payload.get("default_dry_run", False),
                chats=chats,
            )
        except (OSError, JSONDecodeError, TypeError, ValueError) as exc:
            logger.exception("Ошибка чтения конфига: %s", self._path)
            raise AppError(
                "Не удалось прочитать конфиг. Проверьте корректность файла и попробуйте снова."
            ) from exc

    def save(self, config: AppConfig) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(asdict(config), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.exception("Ошибка сохранения конфига: %s", self._path)
            raise AppError("Не удалось сохранить конфиг на диск.") from exc
