"""Abstract interface for system prompt construction and Anti-ChatGPT filters."""

from abc import ABC, abstractmethod
from typing import Any
from discordbuddy.core.events import Event


class IPersonalityManager(ABC):
    """Interface for managing system prompts, vibe rules, and output sanitization."""

    @abstractmethod
    def build_system_prompt(self, context_memories: list[dict[str, Any]] | None = None) -> str:
        """Construct the core system prompt with Anti-ChatGPT guidelines.

        Args:
            context_memories: Optional long-term memories to inject.

        Returns:
            Formatted system prompt string.
        """
        pass

    @abstractmethod
    def format_event_prompt(self, event: Event) -> str:
        """Convert a incoming Event into a concise prompt for the LLM Brain."""
        pass

    @abstractmethod
    def sanitize_response(self, text: str) -> str:
        """Sanitize LLM output enforcing Anti-ChatGPT guidelines and word limits (3-12 words).

        Args:
            text: Raw LLM output string.

        Returns:
            Sanitized, concise response string suitable for TTS playback.
        """
        pass
