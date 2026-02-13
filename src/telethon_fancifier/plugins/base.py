from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class PluginContext:
    chat_id: int
    message_id: int
    dry_run: bool


class Plugin(Protocol):
    plugin_id: str
    title: str

    async def transform(self, text: str, context: PluginContext) -> str:
        ...
