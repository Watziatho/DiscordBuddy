"""Abstract interface for local LLM inference (Qwen3 14B / llama.cpp)."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class IBrain(ABC):
    """Interface for LLM text generation and conversation brain service."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize and load the local GGUF model into VRAM/RAM."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        prompt: str | list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate a text response from the local LLM.

        Args:
            prompt: User message string or Chat Completions messages list.
            system_prompt: Optional overriding system prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Generated response string.
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str | list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int = 100,
    ) -> AsyncGenerator[str, None]:
        """Stream generated response tokens asynchronously.

        Yields:
            Token text chunks.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Unload local model and free VRAM/RAM resources."""
        pass
