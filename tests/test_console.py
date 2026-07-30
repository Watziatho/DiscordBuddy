"""Unit tests for ConsoleUI interactive console mode, history commands, clear, and shutdown."""

import asyncio
import pytest
from discordbuddy.attention.engine import AttentionEngine
from discordbuddy.brain.service import BrainService
from discordbuddy.config.settings import AttentionConfig, BrainConfig, MemoryConfig, VoiceConfig
from discordbuddy.core.conversation_manager import ConversationManager
from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import Event, EventType, UserSpokeEvent, AISpokeEvent
from discordbuddy.memory.store import MemoryStore
from discordbuddy.personality.manager import PersonalityManager
from discordbuddy.ui.console import ConsoleUI
from discordbuddy.voice.pipeline import VoicePipeline


@pytest.mark.asyncio
async def test_console_multiple_turns_and_history_retention(test_event_bus: EventBus, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test multiple conversation turns, memory history retention, and AISpoke responses."""
    brain = BrainService(BrainConfig(enable_diagnostic_check=False))
    await brain.initialize()

    async def mock_gen(prompt, system_prompt=None, max_tokens=None, temperature=None):
        return "That was clean."

    monkeypatch.setattr(brain, "generate_response", mock_gen)

    memory = MemoryStore(MemoryConfig())
    await memory.initialize()

    attention = AttentionEngine(AttentionConfig())
    personality = PersonalityManager()
    voice = VoicePipeline(VoiceConfig(enable_tts_playback=False), test_event_bus)
    await voice.initialize()

    manager = ConversationManager(
        event_bus=test_event_bus,
        attention_engine=attention,
        memory_store=memory,
        personality_manager=personality,
        brain_service=brain,
        voice_pipeline=voice,
    )
    await manager.start()

    console = ConsoleUI(test_event_bus, memory)
    await console.initialize()

    ai_responses: list[AISpokeEvent] = []

    async def ai_handler(event: Event) -> None:
        if isinstance(event, AISpokeEvent):
            ai_responses.append(event)

    test_event_bus.subscribe(EventType.AI_SPOKE, ai_handler)

    # Turn 1
    event1 = UserSpokeEvent(source="console", transcript="Hello there!", is_direct_question=True)
    await test_event_bus.publish(event1)
    await asyncio.sleep(0.2)

    # Turn 2
    event2 = UserSpokeEvent(source="console", transcript="What game is this?", is_direct_question=True)
    await test_event_bus.publish(event2)
    await asyncio.sleep(0.2)

    # Verify AI responses
    assert len(ai_responses) == 2

    # Verify conversation history retention in MemoryStore
    history = await memory.get_conversation_history()
    assert len(history) == 4  # 2 user turns + 2 AI turns
    assert history[0]["speaker"] == "user"
    assert history[0]["text"] == "Hello there!"
    assert history[1]["speaker"] == "ai"
    assert history[1]["text"] == "That was clean."

    await console.shutdown()
    await manager.stop()
    await voice.shutdown()
    await brain.shutdown()
    await memory.close()


@pytest.mark.asyncio
async def test_console_clear_history_command(test_event_bus: EventBus) -> None:
    """Test clearing conversation history."""
    memory = MemoryStore(MemoryConfig())
    await memory.initialize()

    await memory.add_conversation_turn("user", "Hello")
    await memory.add_conversation_turn("ai", "That was clean.")

    history_before = await memory.get_conversation_history()
    assert len(history_before) == 2

    await memory.clear_history()

    history_after = await memory.get_conversation_history()
    assert len(history_after) == 0

    await memory.close()


@pytest.mark.asyncio
async def test_console_ui_graceful_shutdown(test_event_bus: EventBus) -> None:
    """Test ConsoleUI startup and graceful shutdown."""
    memory = MemoryStore(MemoryConfig())
    await memory.initialize()

    console = ConsoleUI(test_event_bus, memory)
    await console.initialize()
    assert console._subscribed is True

    await console.shutdown()
    assert console._subscribed is False
    assert console._is_running is False

    await memory.close()
