"""ConversationManager coordinating event reception, attention, personality context, brain query, and speech synthesis."""

from enum import Enum
from loguru import logger
from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import Event, EventType, UserSpokeEvent
from discordbuddy.core.types import InteractionMode
from discordbuddy.interfaces.attention import IAttentionEngine
from discordbuddy.interfaces.brain import IBrain
from discordbuddy.interfaces.memory import IMemoryStore
from discordbuddy.interfaces.personality import IPersonalityManager
from discordbuddy.interfaces.voice import IVoicePipeline


class ConversationManager:
    """Orchestrates voice conversation flow between EventBus, Attention, Memory, Brain, and Voice."""

    def __init__(
        self,
        event_bus: EventBus,
        attention_engine: IAttentionEngine,
        memory_store: IMemoryStore,
        personality_manager: IPersonalityManager,
        brain_service: IBrain,
        voice_pipeline: IVoicePipeline,
        interaction_mode: InteractionMode = InteractionMode.PASSIVE_DESKTOP,
    ) -> None:
        self.event_bus = event_bus
        self.attention_engine = attention_engine
        self.memory_store = memory_store
        self.personality_manager = personality_manager
        self.brain_service = brain_service
        self.voice_pipeline = voice_pipeline
        self.interaction_mode = interaction_mode
        self._is_subscribed: bool = False

    async def start(self) -> None:
        """Subscribe ConversationManager to UserSpoke and event channels."""
        if self._is_subscribed:
            return
        self.event_bus.subscribe(EventType.USER_SPOKE, self.handle_user_spoke)
        self.event_bus.subscribe_type(UserSpokeEvent, self.handle_user_spoke)
        self._is_subscribed = True
        logger.info(f"ConversationManager started in mode '{self.interaction_mode.value if isinstance(self.interaction_mode, Enum) else self.interaction_mode}'.")

    async def stop(self) -> None:
        """Unsubscribe ConversationManager from event channels."""
        if not self._is_subscribed:
            return
        self.event_bus.unsubscribe(EventType.USER_SPOKE, self.handle_user_spoke)
        self._is_subscribed = False
        logger.info("ConversationManager stopped.")

    async def handle_user_spoke(self, event: Event) -> None:
        """Process incoming UserSpokeEvent."""
        if not isinstance(event, UserSpokeEvent):
            return

        logger.info(f"ConversationManager received UserSpokeEvent: '{event.transcript}'")

        source = getattr(event, "source", "unknown")
        mode = self.interaction_mode
        mode_str = mode.value if isinstance(mode, Enum) else str(mode)

        # Calculate attention score for diagnostic logging
        if hasattr(self.attention_engine, "calculate_score"):
            attention_score = self.attention_engine.calculate_score(event)
        else:
            attention_score = 1.0 if getattr(event, "is_direct_question", False) else 0.0

        # Console-originated events or INTERACTIVE_CONSOLE mode bypass attention gate
        is_console_event = (source == "console")
        is_interactive_mode = (mode_str == InteractionMode.INTERACTIVE_CONSOLE.value)
        bypass_attention = is_console_event or is_interactive_mode

        if bypass_attention:
            should_speak = True
        else:
            should_speak = await self.attention_engine.evaluate_event(event)

        decision_str = "SPEAK" if should_speak else "SILENT"

        # Log detailed routing diagnostic per requirement 6
        logger.debug(
            f"\nSource: {source}\n"
            f"Mode: {mode_str}\n"
            f"Attention score: {attention_score:.2f}\n"
            f"Bypass: {str(bypass_attention).lower()}\n"
            f"Decision: {decision_str}"
        )

        if not should_speak:
            logger.info("ConversationManager decision: SILENT (Attention score below threshold)")
            return

        # 2. Record user turn in memory store and retrieve session history
        await self.memory_store.add_conversation_turn("user", event.transcript)
        history_turns = await self.memory_store.get_conversation_history(limit=6)
        session_context = self._format_session_context(history_turns[:-1])

        # 3. Recall relevant long-term memories
        memories = await self.memory_store.recall_relevant(event.transcript)

        # 4. Build structured Chat Completions messages
        if hasattr(self.personality_manager, "build_event_messages"):
            messages = self.personality_manager.build_event_messages(
                event=event,
                context_memories=memories,
                session_context=session_context,
            )
            raw_response = await self.brain_service.generate_response(prompt=messages)
        else:
            system_prompt = self.personality_manager.build_system_prompt(memories)
            user_prompt = self.personality_manager.format_event_prompt(event)
            raw_response = await self.brain_service.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

        # 5. Sanitize output according to Anti-ChatGPT & length rules
        sanitized_response = self.personality_manager.sanitize_response(raw_response)

        # 6. Record AI response in session memory store
        await self.memory_store.add_conversation_turn("ai", sanitized_response)

        # 7. Speak output via VoicePipeline (triggers AISpokeEvent & audio playback)
        await self.voice_pipeline.speak(sanitized_response)

    def _format_session_context(self, history_turns: list[dict[str, str]]) -> str:
        """Format past session conversation turns for system prompt context."""
        if not history_turns:
            return ""
        formatted = []
        for turn in history_turns:
            role = "User" if turn.get("speaker") == "user" else "Buddy"
            text = turn.get("text", "")
            formatted.append(f"{role}: {text}")
        return "\n".join(formatted)
