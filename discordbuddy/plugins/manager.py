"""Plugin manager for dynamic discovery and lifecycle management."""

from pathlib import Path
from loguru import logger
from discordbuddy.core.event_bus import EventBus
from discordbuddy.plugins.base import BasePlugin


class PluginManager:
    """Discovers, loads, initializes, and controls third-party game plugins."""

    def __init__(self, event_bus: EventBus, plugins_dir: Path | str = "plugins") -> None:
        self.event_bus = event_bus
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: dict[str, BasePlugin] = {}

    async def discover_and_load(self) -> None:
        """Discover plugin directories and instantiate plugin classes."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Searching for plugins in '{self.plugins_dir.resolve()}'")
        # Placeholder for dynamic import and plugin instantiation

    async def start_all(self) -> None:
        """Start all loaded plugins."""
        for name, plugin in self.loaded_plugins.items():
            try:
                await plugin.start()
                logger.info(f"Started plugin '{name}'")
            except Exception as exc:
                logger.error(f"Failed to start plugin '{name}': {exc}")

    async def stop_all(self) -> None:
        """Stop all running plugins."""
        for name, plugin in self.loaded_plugins.items():
            try:
                await plugin.stop()
                logger.info(f"Stopped plugin '{name}'")
            except Exception as exc:
                logger.error(f"Error stopping plugin '{name}': {exc}")
