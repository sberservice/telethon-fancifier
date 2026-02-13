from __future__ import annotations

from telethon_fancifier.core.errors import AppError
from telethon_fancifier.plugins.base import PluginContext
from telethon_fancifier.plugins.llm_rewrite import LlmRewritePlugin
from telethon_fancifier.providers.base import BaseLlmProvider
from telethon_fancifier.providers.deepseek import DeepSeekProvider


async def preview_llm_response(
    text: str,
    chat_id: int = 0,
    provider: BaseLlmProvider | None = None,
) -> str:
    """Возвращает ответ LLM-модуля для текста без запуска Telegram-демона."""
    cleaned = text.strip()
    if not cleaned:
        raise AppError("Текст для LLM-теста пустой. Передайте --text или введите текст в интерактивном режиме.")

    active_provider: BaseLlmProvider = provider if provider is not None else DeepSeekProvider()
    plugin = LlmRewritePlugin(active_provider)
    return await plugin.transform(
        cleaned,
        PluginContext(chat_id=chat_id, message_id=0, dry_run=True),
    )
