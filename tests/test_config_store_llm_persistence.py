from __future__ import annotations

from telethon_fancifier.config.schema import AppConfig, LlmPromptConfig
from telethon_fancifier.config.store import ConfigStore


def test_config_store_persists_custom_llm_prompts(tmp_path) -> None:
    store = ConfigStore()
    store._path = tmp_path / "config.json"

    config = AppConfig()
    config.llm.prompts["glitch"] = LlmPromptConfig(
        system_prompt="glitch-system",
        user_prompt_template="glitch-user: {text}",
        temperature=0.8,
    )
    config.llm.active_prompt = "glitch"

    store.save(config)
    loaded = store.load()

    assert "glitch" in loaded.llm.prompts
    assert loaded.llm.active_prompt == "glitch"
    assert loaded.llm.prompts["glitch"].system_prompt == "glitch-system"
    assert loaded.llm.prompts["glitch"].user_prompt_template == "glitch-user: {text}"
    assert loaded.llm.prompts["glitch"].temperature == 0.8
