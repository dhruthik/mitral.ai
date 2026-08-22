import asyncio
from dataclasses import dataclass

from mitral.models.session import Session
from mitral.server.event_bus import SessionEventBus


@dataclass
class SessionHandle:
    session: Session
    bus: SessionEventBus
    task: asyncio.Task


class SessionStore:
    def __init__(self) -> None:
        self._handles: dict[str, SessionHandle] = {}

    def add(self, handle: SessionHandle) -> None:
        self._handles[handle.session.id] = handle

    def get(self, session_id: str) -> SessionHandle | None:
        return self._handles.get(session_id)


store = SessionStore()
