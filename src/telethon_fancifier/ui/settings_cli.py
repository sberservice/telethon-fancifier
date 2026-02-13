from __future__ import annotations

import logging

from telethon import TelegramClient

from telethon_fancifier.config.schema import AppConfig, ChatConfig
from telethon_fancifier.core.errors import AppError
from telethon_fancifier.core.telegram_credentials import read_telegram_credentials
from telethon_fancifier.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


def merge_chat_configs(existing: list[ChatConfig], updates: list[ChatConfig]) -> list[ChatConfig]:
    """Обновляет только изменённые чаты, сохраняя остальные настройки."""
    updates_by_id = {chat.chat_id: chat for chat in updates}
    existing_ids = {chat.chat_id for chat in existing}

    merged: list[ChatConfig] = []
    for chat in existing:
        merged.append(updates_by_id.get(chat.chat_id, chat))

    for chat in updates:
        if chat.chat_id not in existing_ids:
            merged.append(chat)

    return merged


def remove_chat_configs(existing: list[ChatConfig], remove_indices: list[int]) -> list[ChatConfig]:
    """Удаляет чаты по индексам из текущего списка настроек."""
    remove_set = set(remove_indices)
    return [chat for index, chat in enumerate(existing) if index not in remove_set]


async def fetch_writable_chats() -> list[tuple[int, str]]:
    credentials = read_telegram_credentials()

    chats: list[tuple[int, str]] = []
    try:
        async with TelegramClient(
            credentials.session_name,
            credentials.api_id,
            credentials.api_hash,
        ) as client:
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    chats.append((int(dialog.id), dialog.name or str(dialog.id)))
    except Exception as exc:
        logger.exception("Ошибка получения списка чатов")
        raise AppError(
            "Не удалось получить список чатов из Telegram. Проверьте авторизацию и сеть."
        ) from exc
    return chats


def _pick_indices(total: int, prompt: str, allow_empty: bool = False) -> list[int] | None:
    raw = input(prompt).strip()
    if not raw:
        return None if allow_empty else []
    result: list[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            idx = int(token)
        except ValueError as exc:
            raise AppError(f"Некорректный номер '{token}'. Используйте числа через запятую.") from exc
        if 1 <= idx <= total:
            result.append(idx - 1)
        else:
            raise AppError(f"Номер {idx} вне диапазона 1..{total}.")
    return result


def _print_config_summary(config: AppConfig) -> None:
    print("\nТекущие настройки:")
    if not config.chats:
        print("- Чаты не настроены")
        print()
        return

    for chat in config.chats:
        modules = ", ".join(chat.plugin_order) if chat.plugin_order else "не выбраны"
        print(f"- {chat.title} ({chat.chat_id})")
        print(f"  Модули: {modules}")
    print()


async def _run_add_or_edit_chats_wizard(config: AppConfig, registry: PluginRegistry) -> AppConfig:
    chats = await fetch_writable_chats()
    if not chats:
        print("Не найдено доступных групп/каналов.")
        return config

    configured_by_id = {chat.chat_id: chat for chat in config.chats}

    print("\nДоступные чаты:")
    for i, (chat_id, title) in enumerate(chats, start=1):
        existing = configured_by_id.get(chat_id)
        if existing is None:
            print(f"  {i}. [NEW] {title} ({chat_id})")
            continue

        modules = ", ".join(existing.plugin_order) if existing.plugin_order else "не выбраны"
        print(f"  {i}. [CONFIGURED] {title} ({chat_id}) | модули: {modules}")

    selected = _pick_indices(
        len(chats),
        "Введите номера чатов через запятую (пусто = оставить текущие настройки): ",
        allow_empty=True,
    )
    if selected is None:
        print("Чаты не выбраны. Текущие настройки сохранены без изменений.")
        return config

    selected_chats = [chats[i] for i in selected]

    if not selected_chats:
        raise AppError("Не выбраны корректные номера чатов. Повторите setup.")

    plugin_ids = registry.all_ids()
    print("\nДоступные модули:")
    for i, plugin_id in enumerate(plugin_ids, start=1):
        plugin = registry.get(plugin_id)
        print(f"  {i}. {plugin.plugin_id} — {plugin.title}")

    current_by_id = {chat.chat_id: chat for chat in config.chats}
    updates: list[ChatConfig] = []
    for chat_id, title in selected_chats:
        chosen = _pick_indices(
            len(plugin_ids),
            f"Порядок модулей для '{title}' (например 2,1,3; пусто = оставить как есть): ",
            allow_empty=True,
        )
        existing = current_by_id.get(chat_id)
        if chosen is None:
            order = existing.plugin_order if existing is not None else []
        else:
            order = [plugin_ids[i] for i in chosen]

        updates.append(ChatConfig(chat_id=chat_id, title=title, plugin_order=order))

    config.chats = merge_chat_configs(config.chats, updates)
    _print_config_summary(config)

    return config


async def run_settings_wizard(config: AppConfig, registry: PluginRegistry) -> AppConfig:
    while True:
        print("\n=== Мастер настройки ===")
        print("1. Добавить/изменить чаты и модули")
        print("2. Удалить чаты из конфига")
        print("3. Показать текущие настройки")
        print("0. Завершить setup")

        action = input("Выберите действие: ").strip()
        if action == "1":
            config = await _run_add_or_edit_chats_wizard(config, registry)
            continue
        if action == "2":
            config = run_remove_chats_wizard(config)
            continue
        if action == "3":
            _print_config_summary(config)
            continue
        if action == "0":
            return config

        raise AppError("Неизвестное действие мастера. Используйте 0, 1, 2 или 3.")


def run_remove_chats_wizard(config: AppConfig) -> AppConfig:
    """Интерактивное удаление чатов из текущего конфига."""
    if not config.chats:
        print("В конфиге нет чатов для удаления.")
        return config

    print("\nТекущие настроенные чаты:")
    for i, chat in enumerate(config.chats, start=1):
        modules = ", ".join(chat.plugin_order) if chat.plugin_order else "не выбраны"
        print(f"  {i}. {chat.title} ({chat.chat_id}) | модули: {modules}")

    selected = _pick_indices(
        len(config.chats),
        "Введите номера чатов для удаления через запятую (пусто = отмена): ",
        allow_empty=True,
    )
    if selected is None:
        print("Удаление отменено. Настройки не изменены.")
        return config

    if not selected:
        raise AppError("Не выбраны корректные номера чатов для удаления.")

    config.chats = remove_chat_configs(config.chats, selected)
    print(f"Удалено чатов: {len(set(selected))}.")
    return config
