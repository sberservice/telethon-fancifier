from __future__ import annotations

import pytest

from telethon_fancifier.core.errors import AppError
from telethon_fancifier.core.llm_tools import preview_llm_response
from telethon_fancifier.providers.base import LlmRequest


class FakeProvider:
    async def rewrite(self, request: LlmRequest) -> str:
        return f"echo:{request.chat_id}:{request.text}"


@pytest.mark.asyncio
async def test_preview_llm_response_returns_provider_output() -> None:
    result = await preview_llm_response(
        text="Привет",
        chat_id=42,
        provider=FakeProvider(),
    )
    assert result == "echo:42:Привет"


@pytest.mark.asyncio
async def test_preview_llm_response_rejects_empty_text() -> None:
    with pytest.raises(AppError):
        await preview_llm_response(text="   ", chat_id=1, provider=FakeProvider())
