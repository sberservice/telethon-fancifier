from __future__ import annotations

from datetime import UTC, datetime, timedelta

from telethon_fancifier.core.safeguards import can_edit_last_message


def test_allows_last_message_within_window() -> None:
    date = datetime.now(UTC) - timedelta(seconds=3)
    result = can_edit_last_message(10, 10, date, max_age_seconds=10)
    assert result.ok


def test_rejects_if_not_last_message() -> None:
    date = datetime.now(UTC)
    result = can_edit_last_message(10, 11, date, max_age_seconds=10)
    assert not result.ok


def test_rejects_old_message() -> None:
    date = datetime.now(UTC) - timedelta(seconds=20)
    result = can_edit_last_message(10, 10, date, max_age_seconds=10)
    assert not result.ok
