"""Unit tests for plugin manager lifecycle."""

import pytest
from discordbuddy.core.event_bus import EventBus
from discordbuddy.plugins.base import BasePlugin
from discordbuddy.plugins.manager import PluginManager


class DummyPlugin(BasePlugin):
    """Dummy plugin for testing."""
    name = "DummyPlugin"
    version = "1.0.0"


@pytest.mark.asyncio
async def test_plugin_manager_start_and_stop(test_event_bus: EventBus) -> None:
    """Test registering and starting/stopping plugins."""
    manager = PluginManager(test_event_bus)
    dummy = DummyPlugin(test_event_bus)
    manager.loaded_plugins["DummyPlugin"] = dummy

    await manager.start_all()
    await manager.stop_all()
    assert "DummyPlugin" in manager.loaded_plugins
