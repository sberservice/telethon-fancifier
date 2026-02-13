from __future__ import annotations

from telethon_fancifier.config.schema import LlmConfig
from telethon_fancifier.config.store import ConfigStore
from telethon_fancifier.plugins.base import PluginContext
from telethon_fancifier.providers.base import BaseLlmProvider, LlmRequest


class LlmRewritePlugin:
    plugin_id = "llm_rewrite"
    title = "LLM Rewrite (DeepSeek)"

    def __init__(self, provider: BaseLlmProvider, llm_config: LlmConfig | None = None) -> None:
        self._provider = provider
        self._llm_config = llm_config
        self._config_store = ConfigStore() if llm_config is None else None

    async def transform(self, text: str, context: PluginContext) -> str:
        # Reload config on each transform to see LLM setting changes when running in daemon
        # If llm_config was explicitly provided (e.g., in tests), use that instead
        if self._llm_config is not None:
            llm_config = self._llm_config
        else:
            config = self._config_store.load()  # type: ignore[union-attr]
            llm_config = config.llm
        
        prompt = llm_config.get_active_prompt()
        return await self._provider.rewrite(
            LlmRequest(
                text=text,
                chat_id=context.chat_id,
                system_prompt=prompt.system_prompt,
                user_prompt_template=prompt.user_prompt_template,
                temperature=prompt.temperature,
                model=llm_config.model,
                api_style=llm_config.api_style,
            )
        )
