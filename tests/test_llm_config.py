from __future__ import annotations

import pytest

from telethon_fancifier.config.schema import LlmConfig, LlmPromptConfig
from telethon_fancifier.plugins.base import PluginContext
from telethon_fancifier.plugins.llm_rewrite import LlmRewritePlugin
from telethon_fancifier.providers.base import LlmRequest


class CaptureProvider:
    def __init__(self) -> None:
        self.last_request: LlmRequest | None = None

    async def rewrite(self, request: LlmRequest) -> str:
        self.last_request = request
        return request.text


def test_llm_config_has_default_prompt() -> None:
    config = LlmConfig()

    prompt = config.get_active_prompt()

    assert config.active_prompt == "emoji_mirror"
    assert "{text}" in prompt.user_prompt_template


@pytest.mark.asyncio
async def test_llm_rewrite_passes_prompt_settings_to_provider() -> None:
    provider = CaptureProvider()
    config = LlmConfig(
        model="deepseek-chat",
        api_style="responses",
        active_prompt="friendly",
        prompts={
            "friendly": LlmPromptConfig(
                system_prompt="Be concise",
                user_prompt_template="Rewrite nicely: {text}",
                temperature=0.6,
            )
        },
    )

    plugin = LlmRewritePlugin(provider=provider, llm_config=config)
    transformed = await plugin.transform(
        "hello",
        PluginContext(chat_id=99, message_id=1, dry_run=True),
    )

    assert transformed == "hello"
    assert provider.last_request is not None
    assert provider.last_request.system_prompt == "Be concise"
    assert provider.last_request.user_prompt_template == "Rewrite nicely: {text}"
    assert provider.last_request.temperature == 0.6
    assert provider.last_request.model == "deepseek-chat"
    assert provider.last_request.api_style == "responses"
