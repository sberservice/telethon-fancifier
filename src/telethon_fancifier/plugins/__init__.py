from __future__ import annotations

from telethon_fancifier.config.schema import AppConfig
from telethon_fancifier.plugins.every_second_upper import EverySecondUpperPlugin
from telethon_fancifier.plugins.llm_rewrite import LlmRewritePlugin
from telethon_fancifier.plugins.random_bold import RandomBoldPlugin
from telethon_fancifier.plugins.registry import PluginRegistry
from telethon_fancifier.providers.deepseek import DeepSeekProvider


def build_builtin_registry(config: AppConfig | None = None) -> PluginRegistry:
    registry = PluginRegistry()
    # Don't pass llm_config so the plugin reloads config on each transform
    registry.register(LlmRewritePlugin(provider=DeepSeekProvider(), llm_config=None))
    registry.register(RandomBoldPlugin())
    registry.register(EverySecondUpperPlugin())
    return registry
