from __future__ import annotations

import pytest

from telethon_fancifier.config.schema import AppConfig, LlmPromptConfig
from telethon_fancifier.core.errors import AppError
from telethon_fancifier.plugins.registry import PluginRegistry
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


def test_resolve_prompt_name_supports_number_and_name() -> None:
    prompt_names = ["emoji_mirror", "glitch"]

    assert settings_cli._resolve_prompt_name("1", prompt_names) == "emoji_mirror"
    assert settings_cli._resolve_prompt_name("2", prompt_names) == "glitch"
    assert settings_cli._resolve_prompt_name("glitch", prompt_names) == "glitch"
    assert settings_cli._resolve_prompt_name("9", prompt_names) is None


def test_run_llm_settings_wizard_selects_prompt_by_index(monkeypatch: pytest.MonkeyPatch) -> None:
    config = AppConfig()
    config.llm.prompts["glitch"] = LlmPromptConfig(
        system_prompt="glitch sys",
        user_prompt_template="glitch: {text}",
        temperature=0.1,
    )

    answers = iter(["2", "2", "0"])

    def fake_input(_: str) -> str:
        return next(answers)

    monkeypatch.setattr("builtins.input", fake_input)

    updated = settings_cli.run_llm_settings_wizard(config)

    assert updated is config
    assert config.llm.active_prompt == "glitch"


def test_run_llm_settings_wizard_edit_shows_old_prompt_and_updates(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    config = AppConfig()

    answers = iter(["4", "1", "new system", "new user {text}", "0.7", "0"])

    def fake_input(_: str) -> str:
        return next(answers)

    monkeypatch.setattr("builtins.input", fake_input)

    updated = settings_cli.run_llm_settings_wizard(config)

    assert updated is config
    prompt = config.llm.prompts["emoji_mirror"]
    assert prompt.system_prompt == "new system"
    assert prompt.user_prompt_template == "new user {text}"
    assert prompt.temperature == 0.7

    captured = capsys.readouterr().out
    assert "Текущий system prompt:" in captured
    assert "Текущий user prompt template:" in captured


def test_run_llm_settings_wizard_create_rejects_existing_name(monkeypatch: pytest.MonkeyPatch) -> None:
    config = AppConfig()

    answers = iter(["3", "emoji_mirror"])

    def fake_input(_: str) -> str:
        return next(answers)

    monkeypatch.setattr("builtins.input", fake_input)

    with pytest.raises(AppError):
        settings_cli.run_llm_settings_wizard(config)


def test_run_llm_settings_wizard_calls_on_change_for_model_update(monkeypatch: pytest.MonkeyPatch) -> None:
    config = AppConfig()
    saved: list[str] = []

    answers = iter(["6", "deepseek-reasoner", "0"])

    def fake_input(_: str) -> str:
        return next(answers)

    def on_change(changed_config: AppConfig) -> None:
        saved.append(changed_config.llm.model)

    monkeypatch.setattr("builtins.input", fake_input)

    updated = settings_cli.run_llm_settings_wizard(config, on_change=on_change)

    assert updated is config
    assert config.llm.model == "deepseek-reasoner"
    assert saved == ["deepseek-reasoner"]


@pytest.mark.asyncio
async def test_run_settings_wizard_calls_on_change_after_remove_action(monkeypatch: pytest.MonkeyPatch) -> None:
    config = AppConfig()
    call_count = 0

    def fake_remove_wizard(in_config: AppConfig) -> AppConfig:
        return in_config

    def on_change(_: AppConfig) -> None:
        nonlocal call_count
        call_count += 1

    answers = iter(["2", "0"])

    def fake_input(_: str) -> str:
        return next(answers)

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(settings_cli, "run_remove_chats_wizard", fake_remove_wizard)

    updated = await settings_cli.run_settings_wizard(
        config,
        registry=PluginRegistry(),
        on_change=on_change,
    )

    assert updated is config
    assert call_count == 1
