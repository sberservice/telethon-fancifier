from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def main() -> None:
    if importlib.util.find_spec("PyInstaller") is None:
        print("Ошибка: не найден модуль PyInstaller.")
        print("Установите зависимость командой: pip install pyinstaller")
        sys.exit(2)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        "telethon-fancifier",
        "--collect-all",
        "telethon",
        str(Path(__file__).resolve().parents[1] / "src" / "telethon_fancifier" / "cli.py"),
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        print("Ошибка: сборка portable-версии завершилась с ошибкой.")
        print("Проверьте лог команды выше и повторите запуск.")
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
