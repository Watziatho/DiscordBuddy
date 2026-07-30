"""Abstract interface for the Attention Engine and silence scoring matrix."""

from abc import ABC, abstractmethod
from discordbuddy.core.events import Event


class IAttentionEngine(ABC):
    """Interface for evaluating incoming events and deciding whether the AI should speak."""

    @abstractmethod
    async def evaluate_event(self, event: Event) -> bool:
        """Evaluate an incoming event against attention score matrix and silence tracker.

        Args:
            event: Event instance from EventBus.

        Returns:
            True if AI should proceed to speak, False to remain silent.
        """
        pass

    @abstractmethod
    def calculate_score(self, event: Event) -> float:
        """Calculate numerical attention score for an incoming event."""
        pass

    @abstractmethod
    def update_silence_timer(self) -> None:
        """Reset internal silence timer when user or AI speaks."""
        pass

    @abstractmethod
    def get_silence_duration(self) -> float:
        """Return current seconds elapsed since last audio/speech activity."""
        pass
