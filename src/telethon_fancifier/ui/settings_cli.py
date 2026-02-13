from __future__ import annotations

import logging
from typing import Callable

from telethon import TelegramClient

from telethon_fancifier.config.schema import AppConfig, ChatConfig, LlmPromptConfig
from telethon_fancifier.core.llm_tools import preview_llm_response
from telethon_fancifier.core.errors import AppError
from telethon_fancifier.core.telegram_credentials import read_telegram_credentials
from telethon_fancifier.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


def _notify_config_changed(
    config: AppConfig,
    on_change: Callable[[AppConfig], None] | None,
) -> None:
    if on_change is not None:
        on_change(config)


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
    else:
        for chat in config.chats:
            modules = ", ".join(chat.plugin_order) if chat.plugin_order else "не выбраны"
            print(f"- {chat.title} ({chat.chat_id})")
            print(f"  Модули: {modules}")

    active_prompt = config.llm.prompts.get(config.llm.active_prompt)
    if active_prompt is None:
        active_prompt = config.llm.get_active_prompt()
    print("- LLM:")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Model: {config.llm.model}")
    print(f"  API: {config.llm.api_style}")
    print(f"  Active prompt: {config.llm.active_prompt}")
    print(f"  Temperature: {active_prompt.temperature}")
    print()


def _read_temperature(raw_value: str, *, fallback: float) -> float:
    raw = raw_value.strip()
    if not raw:
        return fallback
    try:
        value = float(raw)
    except ValueError as exc:
        raise AppError("Температура должна быть числом (например 0, 0.2, 1.0).") from exc

    if value < 0 or value > 2:
        raise AppError("Температура должна быть в диапазоне 0..2.")
    return value


def _print_llm_prompts(config: AppConfig) -> None:
    print("\nLLM prompt-профили:")
    for idx, (name, prompt) in enumerate(config.llm.prompts.items(), start=1):
        marker = "*" if name == config.llm.active_prompt else " "
        print(f"  {idx}. [{marker}] {name} | temperature={prompt.temperature}")


def _resolve_prompt_name(raw_value: str, prompt_names: list[str]) -> str | None:
    value = raw_value.strip()
    if not value:
        return None

    if value in prompt_names:
        return value

    if value.isdigit():
        index = int(value) - 1
        if 0 <= index < len(prompt_names):
            return prompt_names[index]

    return None


def run_llm_settings_wizard(
    config: AppConfig,
    on_change: Callable[[AppConfig], None] | None = None,
) -> AppConfig:
    config.llm.get_active_prompt()

    while True:
        print("\n=== Настройки LLM ===")
        print("1. Показать prompt-профили")
        print("2. Выбрать активный prompt")
        print("3. Создать prompt")
        print("4. Изменить prompt")
        print("5. Удалить prompt")
        print("6. Изменить модель")
        print("7. Изменить API-стиль модели")
        print("0. Назад")

        action = input("Выберите действие: ").strip()
        if action == "1":
            _print_llm_prompts(config)
            continue

        if action == "2":
            _print_llm_prompts(config)
            prompt_names = list(config.llm.prompts.keys())
            raw_value = input("Введите имя или номер prompt-профиля: ").strip()
            prompt_name = _resolve_prompt_name(raw_value, prompt_names)
            if prompt_name is None:
                raise AppError(f"Prompt-профиль '{raw_value}' не найден.")
            config.llm.active_prompt = prompt_name
            _notify_config_changed(config, on_change)
            print(f"Активный prompt: {prompt_name}")
            continue

        if action == "3":
            prompt_name = input("Имя prompt-профиля: ").strip()
            if not prompt_name:
                raise AppError("Имя prompt-профиля не может быть пустым.")
            if prompt_name in config.llm.prompts:
                raise AppError(
                    f"Prompt-профиль '{prompt_name}' уже существует. Используйте пункт 'Изменить prompt'."
                )

            system_prompt = input("System prompt: ").strip()
            user_template = input("User prompt template (используйте {text}): ").strip()
            temperature_raw = input("Temperature 0..2 (пусто = 0): ")

            config.llm.prompts[prompt_name] = LlmPromptConfig(
                system_prompt=system_prompt,
                user_prompt_template=user_template if user_template else "{text}",
                temperature=_read_temperature(temperature_raw, fallback=0.0),
            )

            if config.llm.active_prompt not in config.llm.prompts:
                config.llm.active_prompt = prompt_name

            _notify_config_changed(config, on_change)
            print(f"Prompt-профиль '{prompt_name}' создан.")
            continue

        if action == "4":
            _print_llm_prompts(config)
            prompt_names = list(config.llm.prompts.keys())
            raw_value = input("Введите имя или номер prompt-профиля для изменения: ").strip()
            prompt_name = _resolve_prompt_name(raw_value, prompt_names)
            if prompt_name is None:
                raise AppError(f"Prompt-профиль '{raw_value}' не найден.")

            existing = config.llm.prompts.get(prompt_name)
            if existing is None:
                raise AppError(f"Prompt-профиль '{prompt_name}' не найден.")

            current_system = existing.system_prompt
            current_user_template = existing.user_prompt_template
            current_temp = existing.temperature

            print("\nТекущий system prompt:")
            print(current_system)
            print("\nТекущий user prompt template:")
            print(current_user_template)
            print(f"\nТекущая temperature: {current_temp}")

            system_prompt = input(
                "System prompt (пусто = оставить текущее значение): "
            ).strip()
            user_template = input(
                "User prompt template (используйте {text}, пусто = оставить текущее): "
            ).strip()
            temperature_raw = input(
                "Temperature 0..2 (пусто = оставить текущее): "
            )

            config.llm.prompts[prompt_name] = LlmPromptConfig(
                system_prompt=system_prompt if system_prompt else current_system,
                user_prompt_template=user_template if user_template else current_user_template,
                temperature=_read_temperature(temperature_raw, fallback=current_temp),
            )

            if config.llm.active_prompt not in config.llm.prompts:
                config.llm.active_prompt = prompt_name

            _notify_config_changed(config, on_change)
            print(f"Prompt-профиль '{prompt_name}' сохранён.")
            continue

        if action == "5":
            _print_llm_prompts(config)
            prompt_names = list(config.llm.prompts.keys())
            raw_value = input("Введите имя или номер prompt-профиля для удаления: ").strip()
            prompt_name = _resolve_prompt_name(raw_value, prompt_names)
            if prompt_name is None:
                raise AppError(f"Prompt-профиль '{raw_value}' не найден.")
            if len(config.llm.prompts) == 1:
                raise AppError("Нельзя удалить единственный prompt-профиль.")

            del config.llm.prompts[prompt_name]
            if config.llm.active_prompt == prompt_name:
                config.llm.active_prompt = next(iter(config.llm.prompts.keys()))
            _notify_config_changed(config, on_change)
            print(f"Prompt-профиль '{prompt_name}' удалён.")
            continue

        if action == "6":
            model = input("Модель (например deepseek-chat): ").strip()
            if not model:
                raise AppError("Имя модели не может быть пустым.")
            config.llm.model = model
            _notify_config_changed(config, on_change)
            continue

        if action == "7":
            api_style = input("API-стиль (chat_completions или responses): ").strip()
            if api_style not in {"chat_completions", "responses"}:
                raise AppError("Доступные варианты API-стиля: chat_completions, responses.")
            config.llm.api_style = api_style
            _notify_config_changed(config, on_change)
            continue

        if action == "0":
            return config

        raise AppError("Неизвестное действие. Используйте 0, 1, 2, 3, 4, 5, 6 или 7.")


async def run_llm_test_wizard(config: AppConfig) -> AppConfig:
    print("\n=== Тест LLM ===")
    print("Введите текст и получите ответ модели.")
    print("Пустой ввод = назад в мастер настройки.")

    while True:
        source_text = input("Текст для LLM: ").strip()
        if not source_text:
            return config

        result = await preview_llm_response(
            source_text,
            chat_id=0,
            provider=None,
            llm_config=config.llm,
        )
        print("\nLLM запрос:")
        print(source_text)
        print("\nLLM ответ:")
        print(result)


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


async def run_settings_wizard(
    config: AppConfig,
    registry: PluginRegistry,
    on_change: Callable[[AppConfig], None] | None = None,
) -> AppConfig:
    while True:
        print("\n=== Мастер настройки ===")
        print("1. Добавить/изменить чаты и модули")
        print("2. Удалить чаты из конфига")
        print("3. Показать текущие настройки")
        print("4. Настроить LLM prompts/model/temperature")
        print("5. Тест LLM (ввести текст и получить ответ)")
        print("0. Завершить setup")

        action = input("Выберите действие: ").strip()
        if action == "1":
            config = await _run_add_or_edit_chats_wizard(config, registry)
            _notify_config_changed(config, on_change)
            continue
        if action == "2":
            config = run_remove_chats_wizard(config)
            _notify_config_changed(config, on_change)
            continue
        if action == "3":
            _print_config_summary(config)
            continue
        if action == "4":
            config = run_llm_settings_wizard(config, on_change=on_change)
            continue
        if action == "5":
            config = await run_llm_test_wizard(config)
            continue
        if action == "0":
            return config

        raise AppError("Неизвестное действие мастера. Используйте 0, 1, 2, 3, 4 или 5.")


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
