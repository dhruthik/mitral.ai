import asyncio

from mitral.models.events import Event


class SessionEventBus:
    """Durable per-session event log + fanout to live WebSocket subscribers.
    A new subscriber replays `log` first, then receives new events."""

    def __init__(self) -> None:
        self._log: list[Event] = []
        self._subscribers: list[asyncio.Queue] = []
        self._seq = 0

    def publish(self, event: Event) -> None:
        self._seq += 1
        event.seq = self._seq
        self._log.append(event)
        for queue in self._subscribers:
            queue.put_nowait(event)

    def subscribe(self) -> "asyncio.Queue[Event]":
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: "asyncio.Queue[Event]") -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    @property
    def log(self) -> list[Event]:
        return list(self._log)
