from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """Watches config file for changes and triggers reload callbacks."""

    def __init__(self, config_path: Path, check_interval: float = 1.0) -> None:
        """
        Initialize config watcher.
        
        Args:
            config_path: Path to config file to watch
            check_interval: How often to check for changes (seconds)
        """
        self._config_path = config_path
        self._check_interval = check_interval
        self._last_mtime: float | None = None
        self._callbacks: list[Callable[[], None]] = []
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def add_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when config changes."""
        self._callbacks.append(callback)

    async def start(self) -> None:
        """Start watching the config file."""
        if self._running:
            return

        self._running = True
        self._update_mtime()
        self._task = asyncio.create_task(self._watch_loop())
        logger.info("Config watcher started for: %s", self._config_path)

    async def stop(self) -> None:
        """Stop watching the config file."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Config watcher stopped")

    def _update_mtime(self) -> None:
        """Update the last known modification time."""
        try:
            if self._config_path.exists():
                self._last_mtime = self._config_path.stat().st_mtime
        except OSError:
            pass

    async def _watch_loop(self) -> None:
        """Main watch loop that checks for file changes."""
        while self._running:
            await asyncio.sleep(self._check_interval)
            
            try:
                if not self._config_path.exists():
                    continue

                current_mtime = self._config_path.stat().st_mtime
                
                if self._last_mtime is not None and current_mtime > self._last_mtime:
                    logger.info("Config file changed, triggering reload")
                    self._last_mtime = current_mtime
                    
                    # Call all registered callbacks
                    for callback in self._callbacks:
                        try:
                            callback()
                        except Exception:
                            logger.exception("Error in config reload callback")
                
                elif self._last_mtime is None:
                    self._last_mtime = current_mtime

            except OSError:
                logger.exception("Error checking config file")
