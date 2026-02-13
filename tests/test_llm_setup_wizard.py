from __future__ import annotations

import pytest

from telethon_fancifier.config.schema import AppConfig
from telethon_fancifier.ui import settings_cli


@pytest.mark.asyncio
async def test_run_llm_test_wizard_prints_model_reply(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    config = AppConfig()

    answers = iter(["Привет, тест", ""])

    def fake_input(_: str) -> str:
        return next(answers)

    async def fake_preview_llm_response(
        text: str,
        chat_id: int = 0,
        provider: object | None = None,
        llm_config: object | None = None,
    ) -> str:
        assert provider is None
        assert chat_id == 0
        assert llm_config is config.llm
        return f"echo:{text}"

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(settings_cli, "preview_llm_response", fake_preview_llm_response)

    updated = await settings_cli.run_llm_test_wizard(config)

    assert updated is config
    captured = capsys.readouterr().out
    assert "LLM ответ:" in captured
    assert "echo:Привет, тест" in captured
