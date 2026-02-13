from __future__ import annotations

import locale
import platform
import subprocess
import sys
from pathlib import Path

from telethon_fancifier.config.paths import get_data_dir
from telethon_fancifier.core.errors import AppError


def _ensure_windows() -> None:
    if platform.system() != "Windows":
        raise AppError("Команда доступна только на Windows.")


def build_startup_script_content(project_dir: Path, python_executable: str, dry_run: bool) -> str:
    """Формирует содержимое .cmd-файла для автозапуска демона."""
    dry_run_flag = " --dry-run" if dry_run else ""
    return (
        "@echo off\n"
        f'cd /d "{project_dir}"\n'
        f'"{python_executable}" -m telethon_fancifier.cli run{dry_run_flag}\n'
    )


def _startup_script_path(task_name: str) -> Path:
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in task_name)
    return get_data_dir() / "windows" / f"startup_{safe_name}.cmd"


def _decode_process_output(raw: bytes) -> str:
    if not raw:
        return ""

    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            pass

    zero_ratio = raw.count(0) / max(len(raw), 1)
    if zero_ratio > 0.2:
        try:
            return raw.decode("utf-16le")
        except UnicodeDecodeError:
            pass

    preferred = locale.getpreferredencoding(False)
    for encoding in (preferred, "cp866", "cp1251", "utf-8"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    return raw.decode("utf-8", errors="replace")


def _run_command(command: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(command, capture_output=True)
    stdout = _decode_process_output(result.stdout)
    stderr = _decode_process_output(result.stderr)
    return result.returncode, stdout, stderr


def build_install_task_command(task_name: str, script_path: Path) -> list[str]:
    """Формирует команду создания интерактивной задачи (с видимым окном)."""
    return [
        "schtasks",
        "/Create",
        "/SC",
        "ONLOGON",
        "/TN",
        task_name,
        "/TR",
        str(script_path),
        "/IT",
        "/F",
    ]


def install_startup_task(task_name: str, project_dir: Path, dry_run: bool) -> None:
    """Создаёт/обновляет задачу Windows Task Scheduler на автозапуск при входе в систему."""
    _ensure_windows()

    if not project_dir.exists():
        raise AppError(f"Указанная директория проекта не существует: {project_dir}")

    script_path = _startup_script_path(task_name)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        build_startup_script_content(project_dir, sys.executable, dry_run),
        encoding="utf-8",
    )

    create_command = build_install_task_command(task_name, script_path)

    return_code, stdout, stderr = _run_command(create_command)
    if return_code != 0:
        details = (stderr or stdout).strip()
        raise AppError(f"Не удалось создать задачу планировщика. {details}")


def remove_startup_task(task_name: str) -> None:
    """Удаляет задачу автозапуска из Windows Task Scheduler."""
    _ensure_windows()

    delete_command = ["schtasks", "/Delete", "/TN", task_name, "/F"]
    return_code, stdout, stderr = _run_command(delete_command)
    if return_code != 0:
        details = (stderr or stdout).strip()
        raise AppError(f"Не удалось удалить задачу планировщика. {details}")


def get_startup_task_status(task_name: str) -> str:
    """Возвращает подробный статус задачи автозапуска из Task Scheduler."""
    _ensure_windows()

    query_command = ["schtasks", "/Query", "/TN", task_name, "/V", "/FO", "LIST"]
    return_code, stdout, stderr = _run_command(query_command)
    if return_code != 0:
        details = (stderr or stdout).strip()
        raise AppError(f"Не удалось получить статус задачи планировщика. {details}")

    output = stdout.strip()
    if not output:
        raise AppError("Планировщик вернул пустой ответ по задаче.")
    return output
