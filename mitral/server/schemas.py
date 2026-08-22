from pydantic import BaseModel

from mitral.models.personality import Personality


class StartSessionRequest(BaseModel):
    idea: str
    cast: list[Personality] | None = None
    max_rounds_per_room: int | None = None


class StartSessionResponse(BaseModel):
    session_id: str
