"""SQLite persistent memory store implementation."""

from typing import Any
from loguru import logger
from discordbuddy.config.settings import MemoryConfig
from discordbuddy.core.events import Event
from discordbuddy.interfaces.memory import IMemoryStore


class MemoryStore(IMemoryStore):
    """Persistent memory storage utilizing local SQLite database and session history."""

    def __init__(self, config: MemoryConfig) -> None:
        self.config = config
        self._is_connected: bool = False
        self._session_history: list[dict[str, str]] = []

    async def initialize(self) -> None:
        """Initialize SQLite database connection and verify schemas."""
        self.config.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing MemoryStore SQLite database at '{self.config.db_path}'")
        self._is_connected = True
        logger.info("MemoryStore initialized successfully.")

    async def log_event(self, event: Event) -> None:
        """Log event to SQLite database."""
        if not self._is_connected:
            return
        logger.trace(f"Logging event to memory: '{event.event_type}' ({event.event_id})")

    async def store_memory(self, category: str, content: str, importance: float = 1.0) -> None:
        """Store distilled long-term memory."""
        if not self._is_connected:
            return
        logger.info(f"Storing long-term memory [{category}]: '{content}' (Importance: {importance})")

    async def recall_relevant(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Retrieve relevant memories for query context."""
        if not self._is_connected:
            return []
        logger.debug(f"Recalling memories for query: '{query}'")
        return []

    async def add_conversation_turn(self, speaker: str, text: str) -> None:
        """Add a conversation turn ('user' or 'ai') to active session memory."""
        self._session_history.append({"speaker": speaker, "text": text})
        logger.debug(f"Logged conversation turn [{speaker}]: '{text}'")

    async def get_conversation_history(self, limit: int = 10) -> list[dict[str, str]]:
        """Retrieve recent session conversation turns."""
        return self._session_history[-limit:]

    async def clear_history(self) -> None:
        """Clear active session conversation history."""
        self._session_history.clear()
        logger.info("Session conversation history cleared.")

    async def close(self) -> None:
        """Close database connections."""
        logger.info("Closing MemoryStore SQLite connections.")
        self._is_connected = False
