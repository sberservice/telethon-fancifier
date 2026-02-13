from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class SafeguardResult:
    ok: bool
    reason: str = ""


def can_edit_last_message(
    message_id: int,
    last_message_id: int | None,
    message_date: datetime,
    max_age_seconds: int = 10,
) -> SafeguardResult:
    if last_message_id is None:
        return SafeguardResult(False, "В чате нет последнего сообщения для сравнения")
    if message_id != last_message_id:
        return SafeguardResult(False, "Сообщение уже не является последним")

    now = datetime.now(UTC)
    date_utc = message_date if message_date.tzinfo else message_date.replace(tzinfo=UTC)
    age = (now - date_utc).total_seconds()
    if age > max_age_seconds:
        return SafeguardResult(False, f"Сообщение старше {max_age_seconds} секунд")

    return SafeguardResult(True)
