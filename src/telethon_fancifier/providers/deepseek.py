from __future__ import annotations

import logging
import os

import httpx

from telethon_fancifier.providers.base import LlmRequest

logger = logging.getLogger(__name__)


class DeepSeekProvider:
    def __init__(self) -> None:
        self._api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self._base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self._model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    async def rewrite(self, request: LlmRequest) -> str:
        if not self._api_key:
            logger.info("DEEPSEEK_API_KEY не задан, llm_rewrite вернул исходный текст")
            return request.text

        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": "Say nothing yourself. Just mirror user phrases. Add lots of appropriate emoji throughout the message to the user message and send it back. Do not add your own words (this is important)",
                },
                {
                    "role": "user",
                    "content": "Add lots of appropriate emoji throughout (not just at the end, but at the middle of the text) to the following message and just send back the message. Do not add your words. The message is: "
                    + request.text,
                },
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return str(content).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            logger.exception("Ошибка запроса к DeepSeek, возвращен исходный текст")
            return request.text
