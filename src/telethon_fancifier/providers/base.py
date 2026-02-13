from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class LlmRequest:
    text: str
    chat_id: int
    system_prompt: str = ""
    user_prompt_template: str = "{text}"
    temperature: float | None = None
    model: str = ""
    api_style: str = "chat_completions"


class BaseLlmProvider(Protocol):
    async def rewrite(self, request: LlmRequest) -> str:
        ...
