"""Dataclasses and Pydantic event models for the asynchronous event bus."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Supported event categories across the application lifecycle."""

    # Vision events
    BOSS_APPEARED = "vision.boss_appeared"
    FUNNY_DEATH = "vision.funny_death"
    LARGE_EXPLOSION = "vision.large_explosion"
    CUTSCENE_STARTED = "vision.cutscene_started"
    BEAUTIFUL_SCENERY = "vision.beautiful_scenery"
    USER_LAUGHED = "vision.user_laughed"
    SILENCE_TIMEOUT = "vision.silence_timeout"
    GENERIC_VISION = "vision.generic"

    # Voice / Audio events
    USER_SPOKE = "voice.user_spoke"
    AI_SPOKE = "voice.ai_spoke"

    # Attention & State events
    ATTENTION_EVALUATED = "attention.evaluated"
    SHOULD_SPEAK = "attention.should_speak"

    # Memory events
    MEMORY_STORED = "memory.stored"
    MEMORY_RECALLED = "memory.recalled"

    # Plugin events
    GAME_STATE = "plugin.game_state"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class Event(BaseModel):
    """Base Pydantic event structure passed across the central EventBus."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType | str = Field(description="Unique dot-separated event name")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = Field(description="Module or subsystem name generating the event")
    priority: int = Field(default=0, description="Priority integer (higher = processed first)")
    metadata: dict[str, Any] = Field(default_factory=dict)


# --- Vision Event Subclasses ---

class VisionEvent(Event):
    """Base class for all screen capture and VLM extracted visual events."""

    event_type: EventType | str = EventType.GENERIC_VISION
    description: str = Field(description="Human readable summary of what happened on screen")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    visual_tags: list[str] = Field(default_factory=list)


class BossAppearedEvent(VisionEvent):
    """Emitted when a boss entity or massive boss health bar appears."""

    event_type: EventType | str = EventType.BOSS_APPEARED
    boss_name: str | None = Field(default=None)
    health_percentage: float | None = Field(default=None)


class FunnyDeathEvent(VisionEvent):
    """Emitted when the player character dies in a funny or unexpected way."""

    event_type: EventType | str = EventType.FUNNY_DEATH
    cause_of_death: str | None = Field(default=None)


class LargeExplosionEvent(VisionEvent):
    """Emitted when a major particle bloom or sudden large explosion occurs."""

    event_type: EventType | str = EventType.LARGE_EXPLOSION
    intensity: float = Field(default=0.8, ge=0.0, le=1.0)


class CutsceneStartedEvent(VisionEvent):
    """Emitted when a cinematic cutscene begins (HUD disappears / letterboxing)."""

    event_type: EventType | str = EventType.CUTSCENE_STARTED


class BeautifulSceneryEvent(VisionEvent):
    """Emitted when a scenic vista or visually stunning environment is detected."""

    event_type: EventType | str = EventType.BEAUTIFUL_SCENERY


class UserLaughedEvent(VisionEvent):
    """Emitted when visual or audio cues indicate the user is laughing."""

    event_type: EventType | str = EventType.USER_LAUGHED


class SilenceTimeoutEvent(VisionEvent):
    """Emitted when no screen activity or speech has occurred for a duration."""

    event_type: EventType | str = EventType.SILENCE_TIMEOUT
    silence_duration_seconds: float = Field(description="Duration of silence in seconds")


# --- Audio & Voice Events ---

class UserSpokeEvent(Event):
    """Emitted when STT transcribes user speech."""

    event_type: EventType | str = EventType.USER_SPOKE
    transcript: str = Field(description="Transcribed user speech text")
    is_direct_question: bool = Field(default=False)
    confidence: float = Field(default=1.0)


class AISpokeEvent(Event):
    """Emitted when the AI companion synthesizes and speaks a response."""

    event_type: EventType | str = EventType.AI_SPOKE
    text: str = Field(description="Spoken text response")
    word_count: int = Field(description="Word count of response")


# --- Plugin Events ---

class GameStateEvent(Event):
    """Emitted by game plugins delivering direct game telemetry."""

    event_type: EventType | str = EventType.GAME_STATE
    game_name: str = Field(description="Name of game generating telemetry")
    event_name: str = Field(description="Specific game event name")
    data: dict[str, Any] = Field(default_factory=dict)
