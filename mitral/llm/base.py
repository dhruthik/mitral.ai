from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from mitral.models.agent import AgentRuntime
from mitral.models.session import Room, Session


class ToolCallResponse(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = {}


class LLMClient(ABC):
    """Swappable brain behind each agent's turn. Real Claude/Mistral clients
    implement this same interface; MockLLMClient is the zero-key default."""

    @abstractmethod
    async def get_tool_call(
        self,
        *,
        agent: AgentRuntime,
        session: Session,
        room: Room,
        allowed_tools: list[str],
        context: str = "",
    ) -> ToolCallResponse: ...

    @abstractmethod
    async def pitch_line(self, *, agent: AgentRuntime, session: Session, room: Room) -> str: ...

    @abstractmethod
    async def closing_line(
        self, *, agent: AgentRuntime, session: Session, room: Room, votes: dict[str, int]
    ) -> str: ...
