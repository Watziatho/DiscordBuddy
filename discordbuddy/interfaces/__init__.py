"""Abstract interfaces for all DiscordBuddy core modules."""

from discordbuddy.interfaces.brain import IBrain
from discordbuddy.interfaces.vision import IVision
from discordbuddy.interfaces.attention import IAttentionEngine
from discordbuddy.interfaces.memory import IMemoryStore
from discordbuddy.interfaces.personality import IPersonalityManager
from discordbuddy.interfaces.voice import IVoicePipeline
from discordbuddy.interfaces.plugin import IPlugin

__all__ = [
    "IBrain",
    "IVision",
    "IAttentionEngine",
    "IMemoryStore",
    "IPersonalityManager",
    "IVoicePipeline",
    "IPlugin",
]
