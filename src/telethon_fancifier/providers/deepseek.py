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

        model = request.model or self._model
        api_style = request.api_style or "chat_completions"
        user_prompt = self._format_user_prompt(request.user_prompt_template, request.text)

        headers = {"Authorization": f"Bearer {self._api_key}"}
        endpoint, payload = self._build_payload(
            model=model,
            api_style=api_style,
            system_prompt=request.system_prompt,
            user_prompt=user_prompt,
            temperature=request.temperature,
        )
        if endpoint is None or payload is None:
            logger.error("Неподдерживаемый API-стиль для модели: %s", api_style)
            return request.text

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self._base_url}/{endpoint}",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                if api_style == "responses":
                    content = self._extract_responses_content(data)
                else:
                    content = data["choices"][0]["message"]["content"]
                return str(content).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            logger.exception("Ошибка запроса к DeepSeek, возвращен исходный текст")
            return request.text

    @staticmethod
    def _format_user_prompt(template: str, text: str) -> str:
        try:
            return template.format(text=text)
        except (ValueError, KeyError):
            return template + text

    @staticmethod
    def _build_payload(
        model: str,
        api_style: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None,
    ) -> tuple[str | None, dict | None]:
        if api_style == "chat_completions":
            payload: dict[str, object] = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if temperature is not None:
                payload["temperature"] = temperature
            return "chat/completions", payload

        if api_style == "responses":
            payload = {
                "model": model,
                "input": [
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_prompt}],
                    },
                ],
            }
            if temperature is not None:
                payload["temperature"] = temperature
            return "responses", payload

        return None, None

    @staticmethod
    def _extract_responses_content(data: dict) -> str:
        output_text = data.get("output_text")
        if isinstance(output_text, str):
            return output_text
        if isinstance(output_text, list):
            return "".join(str(part) for part in output_text)

        output = data["output"]
        first_item = output[0]
        content = first_item["content"][0]["text"]
        return str(content)
