from __future__ import annotations

from telethon_fancifier.plugins.base import PluginContext
from telethon_fancifier.providers.base import BaseLlmProvider, LlmRequest


class LlmRewritePlugin:
    plugin_id = "llm_rewrite"
    title = "LLM Rewrite (DeepSeek)"

    def __init__(self, provider: BaseLlmProvider) -> None:
        self._provider = provider

    async def transform(self, text: str, context: PluginContext) -> str:
        return await self._provider.rewrite(LlmRequest(text=text, chat_id=context.chat_id))
