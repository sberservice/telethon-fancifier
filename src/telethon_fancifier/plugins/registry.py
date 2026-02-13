from __future__ import annotations

from telethon_fancifier.plugins.base import Plugin
from telethon_fancifier.core.errors import AppError


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.plugin_id] = plugin

    def get(self, plugin_id: str) -> Plugin:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise AppError(f"Модуль '{plugin_id}' не найден в реестре.")
        return plugin

    def all_ids(self) -> list[str]:
        return sorted(self._plugins.keys())

    def all(self) -> list[Plugin]:
        return [self._plugins[key] for key in self.all_ids()]
