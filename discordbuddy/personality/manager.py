"""Personality manager enforcing Anti-ChatGPT guidelines and Discord friend vibe."""

from typing import Any
from loguru import logger
from discordbuddy.core.events import Event, VisionEvent, UserSpokeEvent
from discordbuddy.interfaces.personality import IPersonalityManager
from discordbuddy.personality.prompt_builder import PromptBuilder


class PersonalityManager(IPersonalityManager):
    """Manages prompt engineering via PromptBuilder, Anti-ChatGPT phrase blacklists, and word length limits."""

    FORBIDDEN_PHRASES = [
        "is there anything else",
        "how can i assist",
        "as an ai",
        "i recommend",
        "great job defeating",
        "let me know if you need",
        "would you like me to",
        "user said",
        "keep it short",
        "never explain",
        "instructions",
        "assistant",
    ]

    def __init__(self) -> None:
        self.prompt_builder = PromptBuilder()

    def build_system_prompt(self, context_memories: list[dict[str, Any]] | None = None) -> str:
        """Build system prompt with optional long-term memories."""
        return self.prompt_builder.build_system_prompt(context_memories=context_memories)

    def build_messages(
        self,
        user_input: str,
        context_memories: list[dict[str, Any]] | None = None,
        session_context: str | None = None,
    ) -> list[dict[str, str]]:
        """Construct structured Chat Completions messages list for a user string."""
        return self.prompt_builder.build_messages(
            user_input=user_input,
            context_memories=context_memories,
            session_context=session_context,
        )

    def build_event_messages(
        self,
        event: Event,
        context_memories: list[dict[str, Any]] | None = None,
        session_context: str | None = None,
    ) -> list[dict[str, str]]:
        """Construct structured Chat Completions messages list for an Event."""
        return self.prompt_builder.build_event_messages(
            event=event,
            context_memories=context_memories,
            session_context=session_context,
        )

    def format_event_prompt(self, event: Event) -> str:
        """Legacy helper returning raw event text."""
        if isinstance(event, UserSpokeEvent):
            return event.transcript
        elif isinstance(event, VisionEvent):
            return event.description
        return str(event.event_type)

    def sanitize_response(self, text: str) -> str:
        """Sanitize LLM output to strictly follow Anti-ChatGPT standards."""
        cleaned = text.strip()

        # Strip surrounding quotes if present
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1].strip()

        # Reject forbidden assistant phrases and prompt leakage fragments
        lower_cleaned = cleaned.lower()
        for forbidden in self.FORBIDDEN_PHRASES:
            if forbidden in lower_cleaned:
                logger.warning(f"Sanitizer caught forbidden/leakage phrase '{forbidden}' in: '{cleaned}'")
                return "That was wild."

        # Enforce max word limit (15 words cap)
        words = cleaned.split()
        if len(words) > 15:
            logger.warning(f"Response exceeded max word length ({len(words)} words). Truncating.")
            cleaned = " ".join(words[:10]) + "."

        return cleaned
