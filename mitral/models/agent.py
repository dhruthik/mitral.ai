from typing import Any, Literal

from pydantic import BaseModel

from mitral.models.personality import Personality


class ActionRecord(BaseModel):
    tool: str
    payload: dict[str, Any]
    round: int


class AgentRuntime(BaseModel):
    agent_id: str
    personality: Personality
    room_id: str
    status: Literal["active", "knocked_out"] = "active"
    last_action: ActionRecord | None = None
