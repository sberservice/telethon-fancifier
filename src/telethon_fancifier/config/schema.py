from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ChatConfig:
    chat_id: int
    title: str
    plugin_order: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    schema_version: int = 1
    parse_mode: str = "markdown_v2"
    default_dry_run: bool = False
    chats: list[ChatConfig] = field(default_factory=list)
