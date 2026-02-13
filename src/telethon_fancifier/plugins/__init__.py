from __future__ import annotations

from telethon_fancifier.config.schema import AppConfig
from telethon_fancifier.plugins.every_second_upper import EverySecondUpperPlugin
from telethon_fancifier.plugins.llm_rewrite import LlmRewritePlugin
from telethon_fancifier.plugins.random_bold import RandomBoldPlugin
from telethon_fancifier.plugins.registry import PluginRegistry
from telethon_fancifier.providers.deepseek import DeepSeekProvider


def build_builtin_registry(config: AppConfig | None = None) -> PluginRegistry:
    registry = PluginRegistry()
    # Pass llm_config if available, otherwise plugin will load from disk
    llm_config = config.llm if config is not None else None
    registry.register(LlmRewritePlugin(provider=DeepSeekProvider(), llm_config=llm_config))
    registry.register(RandomBoldPlugin())
    registry.register(EverySecondUpperPlugin())
    return registry
