from __future__ import annotations


class ExampleReversePlugin:
    """Пример внешнего плагина: переворачивает текст посимвольно."""

    plugin_id = "example_reverse"
    title = "Пример: реверс текста"

    async def transform(self, text: str, context: object) -> str:
        return text[::-1]


def get_plugin() -> ExampleReversePlugin:
    return ExampleReversePlugin()
