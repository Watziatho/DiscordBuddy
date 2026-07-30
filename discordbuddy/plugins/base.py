"""Abstract base class for third-party game telemetry plugins."""

from loguru import logger
from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import Event
from discordbuddy.interfaces.plugin import IPlugin


class BasePlugin(IPlugin):
    """Base class for all DiscordBuddy game telemetry plugins."""

    name: str = "BasePlugin"
    version: str = "0.1.0"
    author: str = "Unknown"

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.logger = logger.bind(plugin=self.name)

    async def initialize(self) -> None:
        """Default plugin initialization hook."""
        self.logger.info(f"Initializing plugin '{self.name}' v{self.version}")

    async def start(self) -> None:
        """Default plugin start hook."""
        self.logger.info(f"Starting plugin '{self.name}'")

    async def stop(self) -> None:
        """Default plugin stop hook."""
        self.logger.info(f"Stopping plugin '{self.name}'")

    async def on_event(self, event: Event) -> None:
        """Default event listener hook."""
        pass

    async def publish_event(self, event: Event) -> None:
        """Helper method for plugins to publish events to the central EventBus."""
        await self.event_bus.publish(event)
