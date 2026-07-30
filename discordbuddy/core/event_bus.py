"""Asynchronous in-memory EventBus for publish/subscribe event routing."""

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, TypeVar
from loguru import logger
from discordbuddy.core.events import Event, EventType

EventCallback = Callable[[Event], Awaitable[None]]
E = TypeVar("E", bound=Event)


class EventBus:
    """Central asynchronous EventBus handling event dispatch and subscription.

    Supports wildcard topic matching, priority queues, and async callback handlers.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventCallback]] = defaultdict(list)
        self._type_subscribers: dict[type[Event], list[EventCallback]] = defaultdict(list)
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running: bool = False
        self._worker_task: asyncio.Task[None] | None = None

    def _get_topic_str(self, event_type: EventType | str) -> str:
        """Extract string representation of event type or enum."""
        if hasattr(event_type, "value"):
            return str(getattr(event_type, "value"))
        return str(event_type)

    def subscribe(self, event_type: EventType | str, callback: EventCallback) -> None:
        """Subscribe an async callback to a string event type topic (e.g. 'vision.boss_appeared')."""
        topic = self._get_topic_str(event_type)
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscribed callback '{callback.__name__}' to topic '{topic}'")

    def subscribe_type(self, event_class: type[E], callback: EventCallback) -> None:
        """Subscribe an async callback to a specific Event subclass type."""
        self._type_subscribers[event_class].append(callback)
        logger.debug(f"Subscribed callback '{callback.__name__}' to event class '{event_class.__name__}'")

    def unsubscribe(self, event_type: EventType | str, callback: EventCallback) -> None:
        """Unsubscribe a callback from a string event type topic."""
        topic = self._get_topic_str(event_type)
        if callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)
            logger.debug(f"Unsubscribed callback '{callback.__name__}' from topic '{topic}'")

    async def publish(self, event: Event) -> None:
        """Publish an event to the EventBus queue for async processing."""
        await self._queue.put(event)
        logger.trace(f"Event published to queue: '{event.event_type}' ({event.event_id})")

    async def publish_immediate(self, event: Event) -> None:
        """Immediately dispatch an event to all subscribers without queueing."""
        await self._dispatch(event)

    async def start(self) -> None:
        """Start the background processing loop for queued events."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())
        logger.info("EventBus processing loop started.")

    async def stop(self) -> None:
        """Stop the background processing loop gracefully."""
        if not self._running:
            return
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus processing loop stopped.")

    async def _process_queue(self) -> None:
        """Worker task processing queued events sequentially."""
        while self._running:
            try:
                event = await self._queue.get()
                await self._dispatch(event)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error processing event from queue: {exc}")

    async def _dispatch(self, event: Event) -> None:
        """Internal dispatch mechanism matching subscribers by topic and class."""
        topic = self._get_topic_str(event.event_type)
        callbacks: list[EventCallback] = []

        # Topic string subscribers
        callbacks.extend(self._subscribers.get(topic, []))

        # Wildcard topic subscribers (e.g. 'vision.*')
        prefix = topic.split(".")[0] + ".*" if "." in topic else "*"
        callbacks.extend(self._subscribers.get(prefix, []))
        callbacks.extend(self._subscribers.get("*", []))

        # Class type subscribers
        for event_cls, type_callbacks in self._type_subscribers.items():
            if isinstance(event, event_cls):
                callbacks.extend(type_callbacks)

        if not callbacks:
            logger.trace(f"No subscribers registered for event '{topic}'")
            return

        # Deduplicate callbacks while maintaining order
        unique_callbacks = list(dict.fromkeys(callbacks))

        # Execute callbacks concurrently
        tasks = [asyncio.create_task(self._safe_execute(cb, event)) for cb in unique_callbacks]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_execute(self, callback: EventCallback, event: Event) -> None:
        """Safely execute a callback, catching and logging any unhandled exceptions."""
        try:
            await callback(event)
        except Exception as exc:
            logger.error(
                f"Exception in EventBus callback '{callback.__name__}' processing event '{event.event_type}': {exc}",
                exc_info=True,
            )
