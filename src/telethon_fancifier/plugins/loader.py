from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import ModuleType
from typing import Any

from telethon_fancifier.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


def _load_module_from_path(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Не удалось загрузить модуль: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_external_plugins(registry: PluginRegistry, plugins_dir: Path) -> None:
    if not plugins_dir.exists():
        return

    for file in sorted(plugins_dir.glob("*.py")):
        try:
            module = _load_module_from_path(file)
            factory: Any = getattr(module, "get_plugin", None)
            if callable(factory):
                plugin = factory()
                registry.register(plugin)
                logger.info("Загружен внешний модуль: %s", file.name)
            else:
                logger.warning("Пропуск внешнего модуля без get_plugin(): %s", file.name)
        except Exception:
            logger.exception("Ошибка загрузки внешнего модуля: %s", file)
