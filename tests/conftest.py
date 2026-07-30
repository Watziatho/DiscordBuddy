"""Pytest fixtures for unit testing DiscordBuddy modules."""

import pytest
import pytest_asyncio
from discordbuddy.config.settings import Settings
from discordbuddy.core.event_bus import EventBus


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing instantiated Settings object."""
    return Settings(environment="testing", log_level="DEBUG")


@pytest_asyncio.fixture
async def test_event_bus() -> EventBus:
    """Fixture providing initialized and running EventBus instance."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()
