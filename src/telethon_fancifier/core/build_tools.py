from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

from telethon_fancifier.core.errors import AppError


def run_windows_portable_build() -> None:
    """Запускает локальную сборку portable-версии через существующий скрипт."""
    if platform.system() != "Windows":
        raise AppError(
            "Команда build-windows поддерживает локальную сборку только на Windows. "
            "Для macOS/Linux используйте GitHub Actions workflow '.github/workflows/release.yml'."
        )

    script_path = Path(__file__).resolve().parents[3] / "scripts" / "build_windows_portable.py"
    if not script_path.exists():
        raise AppError(f"Не найден скрипт сборки: {script_path}")

    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
    except subprocess.CalledProcessError as exc:
        raise AppError(
            "Сборка Windows portable завершилась с ошибкой. Проверьте вывод команды выше."
        ) from exc
