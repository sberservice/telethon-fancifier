from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path

from telethon import TelegramClient, events

from telethon_fancifier.config.paths import get_config_path, get_session_dir
from telethon_fancifier.config.schema import AppConfig
from telethon_fancifier.config.store import ConfigStore
from telethon_fancifier.config.watcher import ConfigWatcher
from telethon_fancifier.core.errors import AppError
from telethon_fancifier.core.safeguards import can_edit_last_message
from telethon_fancifier.core.telegram_credentials import read_telegram_credentials
from telethon_fancifier.plugins import build_builtin_registry
from telethon_fancifier.plugins.base import PluginContext
from telethon_fancifier.plugins.loader import load_external_plugins
from telethon_fancifier.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DaemonOptions:
    dry_run: bool = False


class FancifierDaemon:
    def __init__(
        self,
        config: AppConfig,
        registry: PluginRegistry,
        options: DaemonOptions,
        external_plugins_dir: Path | None = None,
        enable_hot_reload: bool = True,
    ) -> None:
        self._config = config
        self._registry = registry
        self._options = options
        self._external_plugins_dir = external_plugins_dir
        self._enable_hot_reload = enable_hot_reload
        self._last_message_by_chat: dict[int, int] = {}
        self._locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._config_store = ConfigStore()
        self._config_watcher: ConfigWatcher | None = None

        # Setup config watcher if enabled
        if self._enable_hot_reload:
            self._config_watcher = ConfigWatcher(get_config_path())
            self._config_watcher.add_callback(self._reload_config)

        credentials = read_telegram_credentials()
        session_dir = get_session_dir()
        session_dir.mkdir(parents=True, exist_ok=True)
        session_path = session_dir / credentials.session_name

        self._client = TelegramClient(
            str(session_path),
            credentials.api_id,
            credentials.api_hash,
        )

    def _reload_config(self) -> None:
        """Reload configuration and rebuild plugin registry."""
        try:
            new_config = self._config_store.load()
            self._config = new_config
            
            # Rebuild registry with new config
            new_registry = build_builtin_registry(new_config)
            if self._external_plugins_dir is not None:
                load_external_plugins(new_registry, self._external_plugins_dir)
            self._registry = new_registry
            
            logger.info("Configuration and plugins reloaded successfully")
        except Exception:  # noqa: BLE001
            logger.exception("Failed to reload configuration, keeping old config")

    def _chat_plugins(self, chat_id: int) -> list[str]:
        for chat in self._config.chats:
            if chat.chat_id == chat_id:
                return chat.plugin_order
        return []

    async def run(self) -> None:
        # Start config watcher if enabled
        if self._config_watcher is not None:
            await self._config_watcher.start()

        @self._client.on(events.NewMessage(outgoing=True))
        async def on_outgoing(event: events.NewMessage.Event) -> None:
            if event.message is None or event.message.id is None or event.chat_id is None:
                return

            chat_id = int(event.chat_id)
            message_id = int(event.message.id)
            text = event.raw_text or ""
            if not text:
                return

            plugin_ids = self._chat_plugins(chat_id)
            if not plugin_ids:
                return

            self._last_message_by_chat[chat_id] = message_id

            async with self._locks[chat_id]:
                guard = can_edit_last_message(
                    message_id=message_id,
                    last_message_id=self._last_message_by_chat.get(chat_id),
                    message_date=event.message.date.astimezone(UTC),
                    max_age_seconds=10,
                )
                if not guard.ok:
                    logger.info("[skip] chat=%s msg=%s: %s", chat_id, message_id, guard.reason)
                    return

                transformed = text
                for plugin_id in plugin_ids:
                    try:
                        plugin = self._registry.get(plugin_id)
                        transformed = await plugin.transform(
                            transformed,
                            PluginContext(
                                chat_id=chat_id,
                                message_id=message_id,
                                dry_run=self._options.dry_run,
                            ),
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.exception("[plugin-error] %s: %s", plugin_id, exc)
                        return

                if transformed == text:
                    return

                if self._options.dry_run:
                    logger.info(
                        "[dry-run] chat=%s msg=%s | before=%s | after=%s",
                        chat_id,
                        message_id,
                        text,
                        transformed,
                    )
                    return

                if self._last_message_by_chat.get(chat_id) != message_id:
                    logger.info(
                        "[skip] chat=%s msg=%s: уже не последнее сообщение",
                        chat_id,
                        message_id,
                    )
                    return

                await self._client.edit_message(chat_id, message_id, transformed, parse_mode="md")

        try:
            await self._client.start()
            logger.info("Демон запущен. Нажмите Ctrl+C для остановки.")
            await self._client.run_until_disconnected()
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Фатальная ошибка демона")
            raise AppError(
                "Демон остановлен из-за ошибки Telegram API/сети. Подробности в логе."
            ) from exc
        finally:
            # Stop config watcher
            if self._config_watcher is not None:
                await self._config_watcher.stop()
