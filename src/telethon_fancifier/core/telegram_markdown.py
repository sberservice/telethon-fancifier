from __future__ import annotations

MDV2_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"


def escape_markdown_v2(text: str) -> str:
    escaped: list[str] = []
    for ch in text:
        if ch in MDV2_SPECIAL_CHARS:
            escaped.append("\\" + ch)
        else:
            escaped.append(ch)
    return "".join(escaped)
