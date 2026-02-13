from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class LlmRequest:
    text: str
    chat_id: int


class BaseLlmProvider(Protocol):
    async def rewrite(self, request: LlmRequest) -> str:
        ...
