from __future__ import annotations

from pathlib import Path

import pytest

from telethon_fancifier.core.errors import AppError
from telethon_fancifier.core.windows_startup import (
    build_install_task_command,
    build_startup_script_content,
    get_startup_task_status,
    remove_startup_task,
)


def test_build_startup_script_content_with_dry_run() -> None:
    content = build_startup_script_content(
        project_dir=Path("C:/proj/telethon-fancifier"),
        python_executable="C:/proj/.venv/Scripts/python.exe",
        dry_run=True,
    )

    assert "cd /d \"C:/proj/telethon-fancifier\"" in content
    assert "-m telethon_fancifier.cli run --dry-run" in content


def test_remove_startup_task_non_windows_raises() -> None:
    with pytest.raises(AppError):
        remove_startup_task("TelethonFancifier")


def test_get_startup_task_status_non_windows_raises() -> None:
    with pytest.raises(AppError):
        get_startup_task_status("TelethonFancifier")


def test_build_install_task_command_sets_interactive_mode() -> None:
    command = build_install_task_command(
        task_name="TelethonFancifier",
        script_path=Path("C:/tmp/startup.cmd"),
    )
    assert "/IT" in command
