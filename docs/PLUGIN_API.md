# DiscordBuddy Plugin API & Integration Guide

## Overview

While DiscordBuddy relies on vision and speech detection out of the box, specialized game telemetry plugins provide **zero-latency, 100% accurate game state events**. 

Plugins allow DiscordBuddy to hook directly into game APIs, log files, memory readers, or companion apps (e.g., Minecraft RCON, CS2 Game State Integration, League of Legends Live Client API).

---

## Plugin Architecture

Plugins inherit from `discordbuddy.plugins.base.BasePlugin` and implement standard lifecycle hooks:

```python
from discordbuddy.plugins.base import BasePlugin
from discordbuddy.core.events import Event, GameStateEvent

class SampleGamePlugin(BasePlugin):
    """Example plugin for reading game telemetry."""

    name = "SampleGamePlugin"
    version = "1.0.0"
    author = "DiscordBuddy Team"

    async def initialize((self) -> None:
        self.logger.info("Initializing SampleGamePlugin...")

    async def start(self) -> None:
        self.logger.info("Starting telemetry monitoring...")
        # Start background polling or socket server

    async def stop(self) -> None:
        self.logger.info("Stopping telemetry monitoring...")

    async def on_event(self, event: Event) -> None:
        # Listen to system events from EventBus
        pass
```

---

## Publishing Events from Plugins

Plugins publish `GameStateEvent` objects directly to the central `EventBus`:

```python
await self.publish_event(
    GameStateEvent(
        source="SampleGamePlugin",
        game_name="Counter-Strike 2",
        event_name="AceClutch",
        data={"kills": 5, "round_type": "clutch"},
        priority=2, # High priority
    )
)
```

---

## Plugin Directory Structure

Plugins are dynamically discovered from the `plugins/` directory:

```
plugins/
└── cs2_telemetry/
    ├── __init__.py
    ├── plugin.py
    └── plugin.toml
```

`plugin.toml` manifest:
```toml
[plugin]
id = "cs2_telemetry"
name = "CS2 Game State Integration"
version = "0.1.0"
entrypoint = "plugin.py:CS2Plugin"
description = "Captures CS2 health, weapon, round events via HTTP POST GSI."
```
