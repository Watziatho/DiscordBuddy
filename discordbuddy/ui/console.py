"""Interactive console UI mode for live terminal conversations with DiscordBuddy."""

import asyncio
import sys
from loguru import logger

from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import Event, EventType, UserSpokeEvent, AISpokeEvent
from discordbuddy.interfaces.memory import IMemoryStore


class ConsoleUI:
    """Interactive console interface for DiscordBuddy acting as an EventBus frontend."""

    def __init__(self, event_bus: EventBus, memory_store: IMemoryStore) -> None:
        self.event_bus = event_bus
        self.memory_store = memory_store
        self._is_running: bool = False
        self._subscribed: bool = False
        self._stop_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize ConsoleUI and subscribe to AISpoke events on the EventBus."""
        if not self._subscribed:
            self.event_bus.subscribe(EventType.AI_SPOKE, self._on_ai_spoke)
            self._subscribed = True
            logger.debug("ConsoleUI subscribed to AISpoke events.")

    async def _on_ai_spoke(self, event: Event) -> None:
        """Handle AISpokeEvent published by VoicePipeline/ConversationManager."""
        if isinstance(event, AISpokeEvent):
            print(f"\nBuddy:\n{event.text}\n")

    async def run_interactive_loop(self) -> None:
        """Run the main async interactive console loop reading user inputs."""
        await self.initialize()
        self._is_running = True

        print("\n====================================")
        print("DiscordBuddy ready.")
        print("Type messages below.")
        print("Type '/exit' to quit.")
        print("====================================\n")

        loop = asyncio.get_running_loop()

        while self._is_running and not self._stop_event.is_set():
            try:
                # Read user input asynchronously from stdin
                user_line = await loop.run_in_executor(None, sys.stdin.readline)
                if not user_line:  # EOF / closed stdin
                    break

                text = user_line.strip()
                if not text:
                    continue

                # Handle console slash commands
                if text.lower() == "/exit":
                    print("\nExiting DiscordBuddy console mode...")
                    self._is_running = False
                    self._stop_event.set()
                    break
                elif text.lower() == "/history":
                    await self._display_history()
                    continue
                elif text.lower() == "/clear":
                    await self.memory_store.clear_history()
                    print("\n[Console] Conversation history cleared.\n")
                    continue

                # Normal user text -> Create UserSpokeEvent & publish to EventBus
                is_question = text.endswith("?")
                event = UserSpokeEvent(
                    source="console",
                    transcript=text,
                    is_direct_question=is_question,
                )
                await self.event_bus.publish(event)

                # Give event bus time to process and yield execution
                await asyncio.sleep(0.1)

            except (KeyboardInterrupt, EOFError):
                print("\nReceived exit signal.")
                self._is_running = False
                self._stop_event.set()
                break
            except Exception as exc:
                logger.error(f"Error in ConsoleUI input loop: {exc}")
                await asyncio.sleep(0.5)

    async def _display_history(self) -> None:
        """Fetch and format conversation history turns."""
        history = await self.memory_store.get_conversation_history(limit=20)
        print("\n--- Current Conversation History ---")
        if not history:
            print("(No conversation history yet)")
        else:
            for turn in history:
                speaker = "User" if turn.get("speaker") == "user" else "Buddy"
                text = turn.get("text", "")
                print(f"[{speaker}]: {text}")
        print("------------------------------------\n")

    async def shutdown(self) -> None:
        """Clean up ConsoleUI subscribers."""
        self._is_running = False
        self._stop_event.set()
        if self._subscribed:
            self.event_bus.unsubscribe(EventType.AI_SPOKE, self._on_ai_spoke)
            self._subscribed = False
            logger.debug("ConsoleUI unsubscribed from AISpoke events.")
