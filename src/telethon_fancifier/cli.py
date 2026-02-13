from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
import sys

from dotenv import load_dotenv

from telethon_fancifier.config.store import ConfigStore
from telethon_fancifier.core.build_tools import run_windows_portable_build
from telethon_fancifier.core.daemon import DaemonOptions, FancifierDaemon
from telethon_fancifier.core.errors import AppError
from telethon_fancifier.core.llm_tools import preview_llm_response
from telethon_fancifier.core.logging_setup import configure_logging
from telethon_fancifier.core.windows_startup import (
    get_startup_task_status,
    install_startup_task,
    remove_startup_task,
)
from telethon_fancifier.plugins import build_builtin_registry
from telethon_fancifier.plugins.loader import load_external_plugins
from telethon_fancifier.ui.settings_cli import run_remove_chats_wizard, run_settings_wizard

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telethon-fancifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("setup", help="Интерактивный мастер: добавить, изменить и удалить чаты")
    subparsers.add_parser("remove-chats", help="Быстро удалить чаты из сохранённых настроек")

    run_parser = subparsers.add_parser("run", help="Запуск демона")
    run_parser.add_argument("--dry-run", action="store_true", help="Показать изменения без редактирования")

    llm_parser = subparsers.add_parser(
        "test-llm",
        help="Проверить ответ LLM-модуля без запуска Telegram",
    )
    llm_parser.add_argument("--text", type=str, help="Текст для отправки в LLM")
    llm_parser.add_argument("--chat-id", type=int, default=0, help="Технический chat_id для контекста")

    subparsers.add_parser("build-windows", help="Собрать portable-версию для Windows")

    startup_install = subparsers.add_parser(
        "install-startup-task",
        help="Добавить автозапуск демона в Windows Task Scheduler",
    )
    startup_install.add_argument(
        "--task-name",
        type=str,
        default="TelethonFancifier",
        help="Имя задачи в планировщике",
    )
    startup_install.add_argument(
        "--project-dir",
        type=str,
        default=str(Path.cwd()),
        help="Путь к директории проекта (где лежит .env)",
    )
    startup_install.add_argument(
        "--dry-run",
        action="store_true",
        help="Запускать демон в режиме --dry-run при автозапуске",
    )

    startup_remove = subparsers.add_parser(
        "remove-startup-task",
        help="Удалить автозапуск демона из Windows Task Scheduler",
    )
    startup_remove.add_argument(
        "--task-name",
        type=str,
        default="TelethonFancifier",
        help="Имя задачи в планировщике",
    )

    startup_status = subparsers.add_parser(
        "startup-task-status",
        help="Показать статус задачи автозапуска в Windows Task Scheduler",
    )
    startup_status.add_argument(
        "--task-name",
        type=str,
        default="TelethonFancifier",
        help="Имя задачи в планировщике",
    )

    subparsers.add_parser("show-config", help="Показать текущий конфиг")
    return parser


def main() -> None:
    log_path = configure_logging()
    load_dotenv()

    parser = _build_parser()
    try:
        args = parser.parse_args()
        if args.command in {"setup", "remove-chats", "show-config", "run"}:
            store = ConfigStore()
            config = store.load()

            registry = build_builtin_registry()
            load_external_plugins(registry, Path("plugins"))

        if args.command == "setup":
            updated = asyncio.run(run_settings_wizard(config, registry))
            store.save(updated)
            print("Настройки сохранены.")
            return

        if args.command == "remove-chats":
            updated = run_remove_chats_wizard(config)
            store.save(updated)
            print("Настройки сохранены.")
            return

        if args.command == "show-config":
            payload = {
                "schema_version": config.schema_version,
                "parse_mode": config.parse_mode,
                "default_dry_run": config.default_dry_run,
                "chats": [
                    {
                        "chat_id": c.chat_id,
                        "title": c.title,
                        "plugin_order": c.plugin_order,
                    }
                    for c in config.chats
                ],
                "plugins": registry.all_ids(),
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        if args.command == "run":
            daemon = FancifierDaemon(
                config=config,
                registry=registry,
                options=DaemonOptions(dry_run=bool(args.dry_run or config.default_dry_run)),
            )
            asyncio.run(daemon.run())
            return

        if args.command == "test-llm":
            source_text = args.text if args.text is not None else input("Введите текст для LLM: ").strip()
            result = asyncio.run(preview_llm_response(source_text, chat_id=args.chat_id))
            print("\nLLM ответ:")
            print(result)
            return

        if args.command == "build-windows":
            run_windows_portable_build()
            print("Сборка завершена. Проверьте директорию dist/.")
            return

        if args.command == "install-startup-task":
            install_startup_task(
                task_name=args.task_name,
                project_dir=Path(args.project_dir).resolve(),
                dry_run=bool(args.dry_run),
            )
            print("Задача автозапуска создана/обновлена.")
            return

        if args.command == "remove-startup-task":
            remove_startup_task(task_name=args.task_name)
            print("Задача автозапуска удалена.")
            return

        if args.command == "startup-task-status":
            status = get_startup_task_status(task_name=args.task_name)
            print(status)
            return
    except AppError as exc:
        print(f"Ошибка: {exc.user_message}")
        print(f"Лог: {log_path}")
        sys.exit(2)
    except KeyboardInterrupt:
        print("Остановлено пользователем.")
        sys.exit(130)
    except Exception:
        logger.exception("Непредвиденная ошибка приложения")
        print("Ошибка: произошла непредвиденная ошибка. Подробности в логе.")
        print(f"Лог: {log_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
