from __future__ import annotations

from telethon_fancifier.config.schema import ChatConfig
from telethon_fancifier.ui.settings_cli import remove_chat_configs


def test_remove_chat_configs_removes_selected_indices() -> None:
    existing = [
        ChatConfig(chat_id=1, title="A", plugin_order=[]),
        ChatConfig(chat_id=2, title="B", plugin_order=[]),
        ChatConfig(chat_id=3, title="C", plugin_order=[]),
    ]

    result = remove_chat_configs(existing, [0, 2])

    assert [chat.chat_id for chat in result] == [2]


def test_remove_chat_configs_empty_selection_keeps_all() -> None:
    existing = [
        ChatConfig(chat_id=1, title="A", plugin_order=[]),
        ChatConfig(chat_id=2, title="B", plugin_order=[]),
    ]

    result = remove_chat_configs(existing, [])

    assert [chat.chat_id for chat in result] == [1, 2]
