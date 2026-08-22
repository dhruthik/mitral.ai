from enum import Enum

from pydantic import BaseModel, Field

from mitral.models.agent import AgentRuntime


class SessionState(str, Enum):
    FORMING = "forming"
    BREAKOUT = "breakout"
    QUORUM = "quorum"
    CONCLUDED = "concluded"


class RoomState(str, Enum):
    ACTIVE = "active"
    CONCLUDED = "concluded"


class Proposal(BaseModel):
    id: str
    room_id: str
    author_id: str
    text: str
    score: int = 0
    upvoted_by: set[str] = Field(default_factory=set)


class Room(BaseModel):
    id: str
    title: str
    tag: str
    color: str
    member_ids: list[str]
    best_proposal_id: str | None = None
    state: RoomState = RoomState.ACTIVE
    round: int = 0
    next_index: int = 0
    forced_next: str | None = None


class QuorumResult(BaseModel):
    winner_room_id: str
    winner_proposal_id: str | None
    tally: dict[str, int]
    closing_line: str


class Session(BaseModel):
    id: str
    idea: str
    agents: dict[str, AgentRuntime]
    rooms: dict[str, Room]
    proposals: dict[str, Proposal] = Field(default_factory=dict)
    state: SessionState = SessionState.FORMING
    max_rounds_per_room: int = 8
    wrap_quorum: float = 0.6
    result: QuorumResult | None = None
