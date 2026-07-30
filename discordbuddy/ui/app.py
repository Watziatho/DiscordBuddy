"""PySide6 desktop UI manager, tray icon, and floating vibe indicator."""

from loguru import logger
from discordbuddy.config.settings import UIConfig


class UIManager:
    """Manages PySide6 application lifecycle, system tray icon, and desktop widgets."""

    def __init__(self, config: UIConfig) -> None:
        self.config = config
        self._is_running: bool = False

    async def initialize(self) -> None:
        """Initialize PySide6 QApplication, system tray icon, and floating overlay."""
        logger.info("Initializing PySide6 UIManager...")
        # Placeholder for PySide6 QApplication & QSystemTrayIcon setup
        logger.info("UIManager initialized successfully.")

    async def start(self) -> None:
        """Show UI components."""
        self._is_running = True
        logger.info("PySide6 Desktop UI running.")

    async def shutdown(self) -> None:
        """Close UI windows and exit QApplication loop."""
        logger.info("Closing PySide6 desktop interface.")
        self._is_running = False
