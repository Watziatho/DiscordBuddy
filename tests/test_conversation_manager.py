"""Unit tests for ConversationManager orchestrator and end-to-end voice conversation flow."""

import asyncio
import pytest
from discordbuddy.attention.engine import AttentionEngine
from discordbuddy.brain.service import BrainService
from discordbuddy.config.settings import AttentionConfig, BrainConfig, MemoryConfig, VoiceConfig
from discordbuddy.core.conversation_manager import ConversationManager
from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import Event, EventType, AISpokeEvent
from discordbuddy.memory.store import MemoryStore
from discordbuddy.personality.manager import PersonalityManager
from discordbuddy.voice.pipeline import VoicePipeline


@pytest.mark.asyncio
async def test_conversation_manager_end_to_end_flow(test_event_bus: EventBus, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test UserSpokeEvent -> ConversationManager -> AISpokeEvent pipeline."""
    brain = BrainService(BrainConfig())
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

    ai_responses: list[AISpokeEvent] = []

    async def ai_spoke_handler(event: Event) -> None:
        if isinstance(event, AISpokeEvent):
            ai_responses.append(event)

    test_event_bus.subscribe(EventType.AI_SPOKE, ai_spoke_handler)

    # Simulate direct user question (guaranteed to speak)
    await voice.simulate_user_speech("What weapon are you using?", is_question=True)
    await asyncio.sleep(0.2)

    assert len(ai_responses) == 1
    assert isinstance(ai_responses[0], AISpokeEvent)
    assert len(ai_responses[0].text) > 0

    await manager.stop()
    await voice.shutdown()
    await brain.shutdown()
    await memory.close()


@pytest.mark.asyncio
async def test_console_message_always_reaches_brain(test_event_bus: EventBus, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test console message (source='console' or INTERACTIVE_CONSOLE mode) bypasses attention gate."""
    from discordbuddy.core.events import UserSpokeEvent
    from discordbuddy.core.types import InteractionMode

    brain_called = False

    async def mock_gen(prompt, **kwargs):
        nonlocal brain_called
        brain_called = True
        return "Clean response."

    brain = BrainService(BrainConfig())
    await brain.initialize()
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
        interaction_mode=InteractionMode.INTERACTIVE_CONSOLE,
    )
    await manager.start()

    # User message without a question mark (normally score=0.0 and suppressed)
    event = UserSpokeEvent(source="console", transcript="hello", is_direct_question=False)
    await test_event_bus.publish(event)
    await asyncio.sleep(0.2)

    assert brain_called is True

    await manager.stop()
    await voice.shutdown()
    await brain.shutdown()
    await memory.close()


@pytest.mark.asyncio
async def test_passive_message_can_be_suppressed(test_event_bus: EventBus, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test passive/desktop message with low attention score is suppressed."""
    from discordbuddy.core.events import UserSpokeEvent
    from discordbuddy.core.types import InteractionMode

    brain_called = False

    async def mock_gen(prompt, **kwargs):
        nonlocal brain_called
        brain_called = True
        return "Clean response."

    brain = BrainService(BrainConfig())
    await brain.initialize()
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
        interaction_mode=InteractionMode.PASSIVE_DESKTOP,
    )
    await manager.start()

    # Non-question speech event in PASSIVE_DESKTOP mode (score < threshold)
    event = UserSpokeEvent(source="passive", transcript="random noise", is_direct_question=False)
    await test_event_bus.publish(event)
    await asyncio.sleep(0.2)

    assert brain_called is False

    await manager.stop()
    await voice.shutdown()
    await brain.shutdown()
    await memory.close()


@pytest.mark.asyncio
async def test_voice_message_uses_attention(test_event_bus: EventBus, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test VOICE_CHAT mode uses attention (questions speak, non-questions below threshold are silent)."""
    from discordbuddy.core.events import UserSpokeEvent
    from discordbuddy.core.types import InteractionMode

    brain_call_count = 0

    async def mock_gen(prompt, **kwargs):
        nonlocal brain_call_count
        brain_call_count += 1
        return "Clean response."

    brain = BrainService(BrainConfig())
    await brain.initialize()
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
        interaction_mode=InteractionMode.VOICE_CHAT,
    )
    await manager.start()

    # 1. Non-question voice speech -> suppressed by attention engine
    event1 = UserSpokeEvent(source="voice", transcript="muttering something", is_direct_question=False)
    await test_event_bus.publish(event1)
    await asyncio.sleep(0.2)
    assert brain_call_count == 0

    # 2. Direct question voice speech -> triggers attention engine decision SPEAK
    event2 = UserSpokeEvent(source="voice", transcript="What game is this?", is_direct_question=True)
    await test_event_bus.publish(event2)
    await asyncio.sleep(0.2)
    assert brain_call_count == 1

    await manager.stop()
    await voice.shutdown()
    await brain.shutdown()
    await memory.close()
