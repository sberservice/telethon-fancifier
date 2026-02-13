from __future__ import annotations

import asyncio

from telethon_fancifier.plugins.base import PluginContext
from telethon_fancifier.plugins.every_second_upper import EverySecondUpperPlugin
from telethon_fancifier.plugins.random_bold import RandomBoldPlugin


def test_every_second_upper() -> None:
    plugin = EverySecondUpperPlugin()
    transformed = asyncio.run(
        plugin.transform("привет", PluginContext(chat_id=1, message_id=1, dry_run=True))
    )
    assert transformed == "пРиВеТ"


def test_random_bold_escapes_markdown() -> None:
    plugin = RandomBoldPlugin(probability=1.0)
    transformed = asyncio.run(
        plugin.transform("a_b", PluginContext(chat_id=1, message_id=1, dry_run=True))
    )
    assert "\\_" in transformed
