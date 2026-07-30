"""Abstract interface for game telemetry plugins."""

from abc import ABC, abstractmethod
from discordbuddy.core.events import Event


class IPlugin(ABC):
    """Abstract interface that all third-party game telemetry plugins must implement."""

    name: str
    version: str
    author: str

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize plugin resources and establish game connections."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start plugin event listener or polling loop."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop plugin execution."""
        pass

    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """Handle incoming events published to the EventBus."""
        pass
