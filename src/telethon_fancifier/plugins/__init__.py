from __future__ import annotations

from telethon_fancifier.plugins.every_second_upper import EverySecondUpperPlugin
from telethon_fancifier.plugins.llm_rewrite import LlmRewritePlugin
from telethon_fancifier.plugins.random_bold import RandomBoldPlugin
from telethon_fancifier.plugins.registry import PluginRegistry
from telethon_fancifier.providers.deepseek import DeepSeekProvider


def build_builtin_registry() -> PluginRegistry:
    registry = PluginRegistry()
    registry.register(LlmRewritePlugin(provider=DeepSeekProvider()))
    registry.register(RandomBoldPlugin())
    registry.register(EverySecondUpperPlugin())
    return registry
