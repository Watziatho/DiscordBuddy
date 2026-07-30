"""Attention engine assessing whether the AI companion should speak."""

import time
from loguru import logger
from discordbuddy.config.settings import AttentionConfig
from discordbuddy.core.events import Event, EventType, VisionEvent, UserSpokeEvent
from discordbuddy.interfaces.attention import IAttentionEngine


class AttentionEngine(IAttentionEngine):
    """Evaluates screen events, user speech, and silence timeouts to determine if AI should speak."""

    def __init__(self, config: AttentionConfig) -> None:
        self.config = config
        self._last_speech_time: float = time.time()
        self._last_spontaneous_speak_time: float = 0.0

    def calculate_score(self, event: Event) -> float:
        """Calculate numerical attention score for an incoming event."""
        if isinstance(event, UserSpokeEvent) and event.is_direct_question:
            return 1.0

        score = 0.0
        if isinstance(event, VisionEvent):
            if event.event_type == EventType.BOSS_APPEARED:
                score += 0.6
            elif event.event_type == EventType.FUNNY_DEATH:
                score += 0.7
            elif event.event_type == EventType.LARGE_EXPLOSION:
                score += 0.4
            elif event.event_type == EventType.BEAUTIFUL_SCENERY:
                score += 0.3
            elif event.event_type == EventType.SILENCE_TIMEOUT:
                score += 0.5

        silence_duration = self.get_silence_duration()
        if silence_duration >= self.config.silence_timeout_seconds:
            score += 0.3

        return score

    async def evaluate_event(self, event: Event) -> bool:
        """Score incoming event against attention rules and return decision."""
        # Direct questions always trigger response
        if isinstance(event, UserSpokeEvent):
            self.update_silence_timer()
            if event.is_direct_question:
                logger.info("Attention decision: SPEAK (User asked direct question)")
                return True

        score = self.calculate_score(event)

        # Spontaneous speak cooldown check
        time_since_last_spoke = time.time() - self._last_spontaneous_speak_time
        if time_since_last_spoke < self.config.spontaneous_cooldown_seconds:
            logger.debug("Attention decision: SILENT (Spontaneous cooldown active)")
            return False

        should_speak = score >= self.config.speaking_score_threshold
        if should_speak:
            self._last_spontaneous_speak_time = time.time()
            logger.info(f"Attention decision: SPEAK (Score: {score:.2f} >= Threshold: {self.config.speaking_score_threshold})")
        else:
            logger.debug(f"Attention decision: SILENT (Score: {score:.2f} < Threshold: {self.config.speaking_score_threshold})")

        return should_speak

    def update_silence_timer(self) -> None:
        """Reset silence timer timestamp."""
        self._last_speech_time = time.time()

    def get_silence_duration(self) -> float:
        """Get seconds elapsed since last speech activity."""
        return time.time() - self._last_speech_time
