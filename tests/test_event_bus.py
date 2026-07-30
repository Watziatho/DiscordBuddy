"""Unit tests for asynchronous EventBus subscriptions and dispatch."""

import asyncio
import pytest
from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import Event, EventType, BossAppearedEvent


@pytest.mark.asyncio
async def test_event_bus_publish_and_subscribe(test_event_bus: EventBus) -> None:
    """Test subscribing to topic and receiving published events."""
    received_events: list[Event] = []

    async def sample_handler(event: Event) -> None:
        received_events.append(event)

    test_event_bus.subscribe(EventType.BOSS_APPEARED, sample_handler)

    test_event = BossAppearedEvent(
        source="test",
        description="Boss spawned",
        boss_name="Malenia",
    )

    await test_event_bus.publish(test_event)
    await asyncio.sleep(0.1)

    assert len(received_events) == 1
    assert received_events[0].event_type == EventType.BOSS_APPEARED
    assert isinstance(received_events[0], BossAppearedEvent)
    assert received_events[0].boss_name == "Malenia"


@pytest.mark.asyncio
async def test_event_bus_wildcard_subscribe(test_event_bus: EventBus) -> None:
    """Test wildcard subscriber receiving all vision events."""
    received_events: list[Event] = []

    async def wildcard_handler(event: Event) -> None:
        received_events.append(event)

    test_event_bus.subscribe("vision.*", wildcard_handler)

    test_event = BossAppearedEvent(
        source="test",
        description="Boss spawned",
    )

    await test_event_bus.publish(test_event)
    await asyncio.sleep(0.1)

    assert len(received_events) == 1
