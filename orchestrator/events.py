"""
Event Bus System

Asynchronous event-driven communication between orchestrator components.
Supports publish/subscribe pattern with filtering and priority.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class EventType(Enum):
    """System event types"""

    # Task Events
    TASK_SUBMITTED = "task.submitted"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    TASK_TIMEOUT = "task.timeout"

    # Security Events
    SECURITY_ALERT = "security.alert"
    SECURITY_VIOLATION = "security.violation"
    AUTHENTICATION_SUCCESS = "auth.success"
    AUTHENTICATION_FAILURE = "auth.failure"

    # System Events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ERROR = "system.error"

    # Component Events
    COMPONENT_REGISTERED = "component.registered"
    COMPONENT_UNREGISTERED = "component.unregistered"
    COMPONENT_ERROR = "component.error"

    # Analysis Events
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"

    # Data Events
    DATA_RECEIVED = "data.received"
    DATA_PROCESSED = "data.processed"
    DATA_EXPORTED = "data.exported"

    # Metrics
    METRICS = "metrics"

    # Custom
    CUSTOM = "custom"


class EventPriority(Enum):
    """Event priority levels"""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class Event:
    """
    Event message

    Attributes:
        type: Event type
        source: Component that emitted the event
        data: Event payload
        priority: Event priority
        timestamp: When the event was created
        id: Unique event ID
        correlation_id: ID to correlate related events
    """

    type: EventType
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }


@dataclass
class Subscription:
    """Event subscription"""

    id: str
    event_type: EventType
    handler: Callable[[Event], None]
    priority_filter: Optional[Set[EventPriority]] = None
    source_filter: Optional[Set[str]] = None

    def matches(self, event: Event) -> bool:
        """Check if subscription matches event"""
        if self.priority_filter and event.priority not in self.priority_filter:
            return False
        if self.source_filter and event.source not in self.source_filter:
            return False
        return True


class EventBus:
    """
    Asynchronous event bus for component communication

    Features:
    - Publish/subscribe pattern
    - Event filtering by priority and source
    - Async handlers
    - Event history
    - Backpressure handling

    Example:
        event_bus = EventBus()
        await event_bus.start()

        # Subscribe to events
        async def handle_task_complete(event):
            print(f"Task completed: {event.data}")

        await event_bus.subscribe(EventType.TASK_COMPLETED, handle_task_complete)

        # Publish event
        await event_bus.publish(Event(
            type=EventType.TASK_COMPLETED,
            source="task_manager",
            data={"task_id": "123"}
        ))
    """

    def __init__(self, max_queue_size: int = 10000, history_size: int = 1000):
        self.max_queue_size = max_queue_size
        self.history_size = history_size

        # Subscriptions
        self._subscriptions: Dict[EventType, List[Subscription]] = {
            event_type: [] for event_type in EventType
        }
        self._subscription_counter = 0

        # Event queue
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)

        # Event history
        self._history: List[Event] = []

        # Runtime
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # Statistics
        self._published = 0
        self._delivered = 0
        self._dropped = 0

    async def start(self) -> None:
        """Start the event bus"""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())

    async def stop(self) -> None:
        """Stop the event bus"""
        if not self._running:
            return

        self._running = False

        # Wait for queue to drain
        await self._queue.join()

        # Cancel worker
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    @property
    def is_running(self) -> bool:
        """Check if event bus is running"""
        return self._running

    # ==================== Subscription Management ====================

    async def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
        priority_filter: Optional[List[EventPriority]] = None,
        source_filter: Optional[List[str]] = None,
    ) -> str:
        """
        Subscribe to events

        Args:
            event_type: Type of events to subscribe to
            handler: Async callback function
            priority_filter: Only receive events with these priorities
            source_filter: Only receive events from these sources

        Returns:
            Subscription ID
        """
        async with self._lock:
            self._subscription_counter += 1
            sub_id = f"sub-{self._subscription_counter}"

            subscription = Subscription(
                id=sub_id,
                event_type=event_type,
                handler=handler,
                priority_filter=(
                    set(priority_filter) if priority_filter else None
                ),
                source_filter=set(source_filter) if source_filter else None,
            )

            self._subscriptions[event_type].append(subscription)

            return sub_id

    async def unsubscribe(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> bool:
        """Unsubscribe from events"""
        async with self._lock:
            subs = self._subscriptions[event_type]
            for i, sub in enumerate(subs):
                if sub.handler == handler:
                    subs.pop(i)
                    return True
            return False

    async def unsubscribe_by_id(self, subscription_id: str) -> bool:
        """Unsubscribe by subscription ID"""
        async with self._lock:
            for event_type, subs in self._subscriptions.items():
                for i, sub in enumerate(subs):
                    if sub.id == subscription_id:
                        subs.pop(i)
                        return True
            return False

    # ==================== Event Publishing ====================

    async def publish(self, event: Event) -> bool:
        """
        Publish an event

        Args:
            event: Event to publish

        Returns:
            True if event was queued
        """
        if not self._running:
            return False

        try:
            self._queue.put_nowait(event)
            self._published += 1
            return True
        except asyncio.QueueFull:
            self._dropped += 1
            return False

    async def publish_immediate(self, event: Event) -> None:
        """
        Publish and process event immediately (bypass queue)

        Use sparingly for critical events only.
        """
        await self._deliver_event(event)

    # ==================== Event Processing ====================

    async def _process_events(self) -> None:
        """Main event processing loop"""
        while self._running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                # Process event
                await self._deliver_event(event)

                # Add to history
                self._add_to_history(event)

                # Mark as done
                self._queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Event processing error: {e}")

    async def _deliver_event(self, event: Event) -> None:
        """Deliver event to all matching subscribers"""
        async with self._lock:
            subscribers = self._subscriptions.get(event.type, []).copy()

        # Call handlers concurrently
        tasks = []
        for sub in subscribers:
            if sub.matches(event):
                task = asyncio.create_task(
                    self._call_handler(sub.handler, event)
                )
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            self._delivered += len(tasks)

    async def _call_handler(
        self, handler: Callable[[Event], None], event: Event
    ) -> None:
        """Call event handler with error handling"""
        try:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            print(f"Handler error for {event.type.value}: {e}")

    def _add_to_history(self, event: Event) -> None:
        """Add event to history"""
        self._history.append(event)

        # Trim history
        if len(self._history) > self.history_size:
            self._history = self._history[-self.history_size :]

    # ==================== Event History ====================

    async def get_history(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Get event history with filtering"""
        history = self._history

        if event_type:
            history = [e for e in history if e.type == event_type]

        if source:
            history = [e for e in history if e.source == source]

        return history[-limit:]

    async def clear_history(self) -> None:
        """Clear event history"""
        self._history.clear()

    # ==================== Statistics ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            "published": self._published,
            "delivered": self._delivered,
            "dropped": self._dropped,
            "queue_size": self._queue.qsize(),
            "history_size": len(self._history),
            "subscriptions": sum(
                len(subs) for subs in self._subscriptions.values()
            ),
        }

    # ==================== Utility ====================

    async def wait_for_event(
        self,
        event_type: EventType,
        timeout: Optional[float] = None,
        predicate: Optional[Callable[[Event], bool]] = None,
    ) -> Optional[Event]:
        """
        Wait for a specific event

        Args:
            event_type: Type of event to wait for
            timeout: Maximum time to wait (seconds)
            predicate: Optional filter function

        Returns:
            Event if found, None if timeout
        """
        future = asyncio.Future()

        async def handler(event: Event) -> None:
            if not predicate or predicate(event):
                if not future.done():
                    future.set_result(event)

        # Subscribe
        sub_id = await self.subscribe(event_type, handler)

        try:
            if timeout:
                return await asyncio.wait_for(future, timeout=timeout)
            else:
                return await future
        except asyncio.TimeoutError:
            return None
        finally:
            await self.unsubscribe_by_id(sub_id)


class EventStream:
    """
    Streaming event consumer

    Provides async iterator interface for consuming events.
    """

    def __init__(
        self,
        event_bus: EventBus,
        event_types: List[EventType],
        buffer_size: int = 100,
    ):
        self.event_bus = event_bus
        self.event_types = event_types
        self.buffer: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        self._subscription_ids: List[str] = []
        self._running = False

    async def start(self) -> None:
        """Start the event stream"""
        self._running = True

        for event_type in self.event_types:
            sub_id = await self.event_bus.subscribe(event_type, self._on_event)
            self._subscription_ids.append(sub_id)

    async def stop(self) -> None:
        """Stop the event stream"""
        self._running = False

        for sub_id in self._subscription_ids:
            await self.event_bus.unsubscribe_by_id(sub_id)

        self._subscription_ids.clear()

    async def _on_event(self, event: Event) -> None:
        """Handle incoming event"""
        try:
            self.buffer.put_nowait(event)
        except asyncio.QueueFull:
            pass  # Drop oldest or new event

    def __aiter__(self):
        return self

    async def __anext__(self) -> Event:
        if not self._running:
            raise StopAsyncIteration

        event = await self.buffer.get()
        return event
