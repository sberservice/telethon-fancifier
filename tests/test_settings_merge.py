from __future__ import annotations

from telethon_fancifier.config.schema import ChatConfig
from telethon_fancifier.ui.settings_cli import merge_chat_configs


def test_merge_preserves_unselected_chats() -> None:
    existing = [
        ChatConfig(chat_id=1, title="A", plugin_order=["random_bold"]),
        ChatConfig(chat_id=2, title="B", plugin_order=["every_second_upper"]),
    ]
    updates = [
        ChatConfig(chat_id=2, title="B", plugin_order=["llm_rewrite"]),
    ]

    merged = merge_chat_configs(existing, updates)

    assert [c.chat_id for c in merged] == [1, 2]
    assert merged[0].plugin_order == ["random_bold"]
    assert merged[1].plugin_order == ["llm_rewrite"]


def test_merge_appends_new_chat() -> None:
    existing = [
        ChatConfig(chat_id=1, title="A", plugin_order=["random_bold"]),
    ]
    updates = [
        ChatConfig(chat_id=3, title="C", plugin_order=["every_second_upper"]),
    ]

    merged = merge_chat_configs(existing, updates)

    assert [c.chat_id for c in merged] == [1, 3]
    assert merged[1].plugin_order == ["every_second_upper"]
