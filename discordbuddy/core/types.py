"""Core type definitions and Enums for DiscordBuddy."""

from enum import Enum


class InteractionMode(str, Enum):
    """Interaction modes defining user input routing and attention behavior."""

    PASSIVE_DESKTOP = "PASSIVE_DESKTOP"
    INTERACTIVE_CONSOLE = "INTERACTIVE_CONSOLE"
    VOICE_CHAT = "VOICE_CHAT"
