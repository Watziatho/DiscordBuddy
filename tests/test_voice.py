"""Unit tests for VoicePipeline speech input simulation and TTS output execution."""

import asyncio
import pytest
from discordbuddy.config.settings import VoiceConfig
from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import Event, EventType, UserSpokeEvent, AISpokeEvent
from discordbuddy.voice.pipeline import VoicePipeline


@pytest.mark.asyncio
async def test_voice_pipeline_speak_publishes_event(test_event_bus: EventBus) -> None:
    """Test VoicePipeline.speak() publishes AISpokeEvent."""
    voice = VoicePipeline(VoiceConfig(enable_tts_playback=False), test_event_bus)
    await voice.initialize()

    published_events: list[Event] = []

    async def ai_handler(event: Event) -> None:
        published_events.append(event)

    test_event_bus.subscribe(EventType.AI_SPOKE, ai_handler)

    await voice.speak("Bro got deleted.")
    await asyncio.sleep(0.1)

    assert len(published_events) == 1
    assert isinstance(published_events[0], AISpokeEvent)
    assert published_events[0].text == "Bro got deleted."
    assert published_events[0].word_count == 3

    await voice.shutdown()


@pytest.mark.asyncio
async def test_voice_pipeline_user_speech_simulation(test_event_bus: EventBus) -> None:
    """Test simulate_user_speech publishes UserSpokeEvent."""
    voice = VoicePipeline(VoiceConfig(), test_event_bus)
    await voice.initialize()

    user_events: list[Event] = []

    async def user_handler(event: Event) -> None:
        user_events.append(event)

    test_event_bus.subscribe(EventType.USER_SPOKE, user_handler)

    await voice.simulate_user_speech("Nice clutch!", is_question=False)
    await asyncio.sleep(0.1)

    assert len(user_events) == 1
    assert isinstance(user_events[0], UserSpokeEvent)
    assert user_events[0].transcript == "Nice clutch!"

    await voice.shutdown()
