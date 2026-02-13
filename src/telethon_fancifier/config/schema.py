from __future__ import annotations

from dataclasses import dataclass, field


def _default_llm_prompts() -> dict[str, "LlmPromptConfig"]:
    return {
        "emoji_mirror": LlmPromptConfig(
            system_prompt=(
                "Say nothing yourself. Just mirror user phrases. Add lots of appropriate "
                "emoji throughout the message to the user message and send it back. "
                "Do not add your own words (this is important)"
            ),
            user_prompt_template=(
                "Add lots of appropriate emoji throughout (not just at the end, but at the "
                "middle of the text) to the following message and just send back the message. "
                "Do not add your words. The message is: {text}"
            ),
            temperature=0.0,
        )
    }


@dataclass(slots=True)
class LlmPromptConfig:
    system_prompt: str
    user_prompt_template: str
    temperature: float = 0.0


@dataclass(slots=True)
class LlmConfig:
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    api_style: str = "chat_completions"
    active_prompt: str = "emoji_mirror"
    prompts: dict[str, LlmPromptConfig] = field(default_factory=_default_llm_prompts)

    def get_active_prompt(self) -> LlmPromptConfig:
        prompt = self.prompts.get(self.active_prompt)
        if prompt is not None:
            return prompt

        first_prompt = next(iter(self.prompts.values()), None)
        if first_prompt is not None:
            return first_prompt

        fallback = _default_llm_prompts()
        self.prompts = fallback
        self.active_prompt = next(iter(fallback.keys()))
        return fallback[self.active_prompt]


@dataclass(slots=True)
class ChatConfig:
    chat_id: int
    title: str
    plugin_order: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    schema_version: int = 1
    parse_mode: str = "markdown_v2"
    default_dry_run: bool = False
    chats: list[ChatConfig] = field(default_factory=list)
    llm: LlmConfig = field(default_factory=LlmConfig)
