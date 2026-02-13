from __future__ import annotations

import random

from telethon_fancifier.core.telegram_markdown import escape_markdown_v2
from telethon_fancifier.plugins.base import PluginContext


class RandomBoldPlugin:
    plugin_id = "random_bold"
    title = "Случайный жирный markdown"

    def __init__(self, probability: float = 0.18) -> None:
        self._probability = probability

    async def transform(self, text: str, context: PluginContext) -> str:
        escaped = escape_markdown_v2(text)
        result: list[str] = []
        for ch in escaped:
            if ch.isalpha() and random.random() < self._probability:
                result.append(f"*{ch}*")
            else:
                result.append(ch)
        return "".join(result)
