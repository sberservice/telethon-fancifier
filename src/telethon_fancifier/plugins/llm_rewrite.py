from __future__ import annotations

from telethon_fancifier.config.schema import LlmConfig
from telethon_fancifier.plugins.base import PluginContext
from telethon_fancifier.providers.base import BaseLlmProvider, LlmRequest


class LlmRewritePlugin:
    plugin_id = "llm_rewrite"
    title = "LLM Rewrite (DeepSeek)"

    def __init__(self, provider: BaseLlmProvider, llm_config: LlmConfig | None = None) -> None:
        self._provider = provider
        self._llm_config = llm_config if llm_config is not None else LlmConfig()

    async def transform(self, text: str, context: PluginContext) -> str:
        prompt = self._llm_config.get_active_prompt()
        return await self._provider.rewrite(
            LlmRequest(
                text=text,
                chat_id=context.chat_id,
                system_prompt=prompt.system_prompt,
                user_prompt_template=prompt.user_prompt_template,
                temperature=prompt.temperature,
                model=self._llm_config.model,
                api_style=self._llm_config.api_style,
            )
        )
