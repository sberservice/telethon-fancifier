from __future__ import annotations

from telethon_fancifier.plugins.base import PluginContext


class EverySecondUpperPlugin:
    plugin_id = "every_second_upper"
    title = "Каждая вторая буква заглавная"

    async def transform(self, text: str, context: PluginContext) -> str:
        chars: list[str] = []
        letter_index = 0
        for ch in text:
            if ch.isalpha():
                chars.append(ch.upper() if letter_index % 2 == 1 else ch.lower())
                letter_index += 1
            else:
                chars.append(ch)
        return "".join(chars)
