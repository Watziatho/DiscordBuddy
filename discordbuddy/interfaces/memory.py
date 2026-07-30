"""Abstract interface for local SQLite memory storage and session logs."""

from abc import ABC, abstractmethod
from typing import Any
from discordbuddy.core.events import Event


class IMemoryStore(ABC):
    """Interface for persistent SQLite storage and memory recall."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database connections and execute schema migrations."""
        pass

    @abstractmethod
    async def log_event(self, event: Event) -> None:
        """Log an event from the EventBus to the persistent database."""
        pass

    @abstractmethod
    async def store_memory(self, category: str, content: str, importance: float = 1.0) -> None:
        """Store a distilled long-term memory fact or inside joke."""
        pass

    @abstractmethod
    async def recall_relevant(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Retrieve relevant memories matching a query context.

        Args:
            query: Topic or query text.
            limit: Maximum memories to return.

        Returns:
            List of memory dictionaries.
        """
        pass

    @abstractmethod
    async def add_conversation_turn(self, speaker: str, text: str) -> None:
        """Log a conversation turn ('user' or 'ai') into session memory."""
        pass

    @abstractmethod
    async def get_conversation_history(self, limit: int = 10) -> list[dict[str, str]]:
        """Retrieve recent session conversation history turns."""
        pass

    @abstractmethod
    async def clear_history(self) -> None:
        """Clear session conversation history."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connection pool gracefully."""
        pass
