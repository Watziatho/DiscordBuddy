"""Main application entrypoint initializing settings, logging, EventBus, and modules."""

import asyncio
import sys
from loguru import logger

from discordbuddy.config.loader import load_settings
from discordbuddy.core.conversation_manager import ConversationManager
from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import Event, EventType
from discordbuddy.core.types import InteractionMode
from discordbuddy.utils.logging import setup_logging

from discordbuddy.brain.service import BrainService
from discordbuddy.vision.service import VisionService
from discordbuddy.attention.engine import AttentionEngine
from discordbuddy.memory.store import MemoryStore
from discordbuddy.personality.manager import PersonalityManager
from discordbuddy.voice.pipeline import VoicePipeline
from discordbuddy.plugins.manager import PluginManager
from discordbuddy.ui.app import UIManager
from discordbuddy.ui.console import ConsoleUI


class Application:
    """DiscordBuddy main application container managing service lifecycles."""

    def __init__(self) -> None:
        self.settings = load_settings()
        setup_logging(log_level=self.settings.log_level)

        # Detect interaction mode from settings or CLI flags
        if self.settings.ui.interactive_console or "--console" in sys.argv:
            self.settings.interaction_mode = InteractionMode.INTERACTIVE_CONSOLE

        logger.info(f"=== Starting {self.settings.app_name} ===")
        logger.info(f"Interaction Mode: {self.settings.interaction_mode.value}")
        logger.info(f"Target GPU: {self.settings.hardware.gpu_name}")
        logger.info(f"Target CPU: {self.settings.hardware.cpu_name}")

        # Core EventBus
        self.event_bus = EventBus()

        # Module services
        self.brain = BrainService(self.settings.brain)
        self.vision = VisionService(self.settings.vision, self.event_bus)
        self.attention = AttentionEngine(self.settings.attention)
        self.memory = MemoryStore(self.settings.memory)
        self.personality = PersonalityManager()
        self.voice = VoicePipeline(self.settings.voice, self.event_bus)
        self.plugin_manager = PluginManager(self.event_bus)
        self.ui = UIManager(self.settings.ui)
        self.console_ui = ConsoleUI(self.event_bus, self.memory)

        # Conversation Orchestrator
        self.conversation_manager = ConversationManager(
            event_bus=self.event_bus,
            attention_engine=self.attention,
            memory_store=self.memory,
            personality_manager=self.personality,
            brain_service=self.brain,
            voice_pipeline=self.voice,
            interaction_mode=self.settings.interaction_mode,
        )

    async def start(self) -> None:
        """Initialize all subsystems, bind event listeners, and start processing."""
        logger.info("Initializing application subsystems...")

        # 1. Start EventBus
        await self.event_bus.start()

        # 2. Initialize storage & state managers
        await self.memory.initialize()
        await self.brain.initialize()

        # 3. Initialize vision & voice pipelines
        await self.vision.initialize()
        await self.voice.initialize()

        # 4. Discover plugins & initialize UI
        await self.plugin_manager.discover_and_load()
        await self.ui.initialize()

        # 5. Start ConversationManager orchestrator
        await self.conversation_manager.start()

        # 6. Bind memory logger subscriber
        self.event_bus.subscribe("*", self._on_any_event)

        # 7. Publish startup event
        startup_event = Event(
            event_type=EventType.SYSTEM_STARTUP,
            source="main",
            metadata={"app_name": self.settings.app_name},
        )
        await self.event_bus.publish(startup_event)

        logger.info("=== All DiscordBuddy subsystems initialized successfully ===")

    async def _on_any_event(self, event: Event) -> None:
        """Global event logger and memory handler."""
        await self.memory.log_event(event)

    async def shutdown(self) -> None:
        """Gracefully shut down all application subsystems."""
        logger.info("=== Shutting down DiscordBuddy ===")

        # Send shutdown event
        shutdown_event = Event(
            event_type=EventType.SYSTEM_SHUTDOWN,
            source="main",
        )
        await self.event_bus.publish_immediate(shutdown_event)

        # Stop services in reverse order
        await self.console_ui.shutdown()
        await self.conversation_manager.stop()
        await self.ui.shutdown()
        await self.plugin_manager.stop_all()
        await self.voice.shutdown()
        await self.vision.shutdown()
        await self.brain.shutdown()
        await self.memory.close()
        await self.event_bus.stop()

        logger.info("=== DiscordBuddy shutdown complete ===")


async def run_app() -> None:
    """Async main entrypoint managing startup and graceful shutdown."""
    app = Application()
    is_console_mode = app.settings.interaction_mode == InteractionMode.INTERACTIVE_CONSOLE
    try:
        await app.start()
        if is_console_mode:
            await app.console_ui.run_interactive_loop()
        else:
            # Brief sleep for non-interactive test run
            await asyncio.sleep(0.5)
    except Exception as exc:
        logger.critical(f"Unhandled exception in main loop: {exc}", exc_info=True)
    finally:
        await app.shutdown()


def main() -> int:
    """Synchronous CLI entrypoint."""
    try:
        asyncio.run(run_app())
        return 0
    except KeyboardInterrupt:
        logger.info("Received exit signal (KeyboardInterrupt).")
        return 0
    except Exception as exc:
        logger.critical(f"Fatal startup failure: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
