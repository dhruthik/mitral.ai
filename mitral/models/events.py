import time
import uuid
from typing import Literal, Union

from pydantic import BaseModel, Field


def _new_id() -> str:
    return uuid.uuid4().hex


class EventBase(BaseModel):
    id: str = Field(default_factory=_new_id)
    session_id: str
    seq: int = 0
    ts: float = Field(default_factory=time.time)


class SessionStarted(EventBase):
    type: Literal["session_started"] = "session_started"
    idea: str
    roster: list[dict]
    max_rounds_per_room: int


class RoomFormed(EventBase):
    type: Literal["room_formed"] = "room_formed"
    room_id: str
    title: str
    tag: str
    color: str
    member_ids: list[str]


class TurnStarted(EventBase):
    type: Literal["turn_started"] = "turn_started"
    room_id: str
    agent_id: str
    round: int


class MessageSent(EventBase):
    type: Literal["message_sent"] = "message_sent"
    room_id: str
    agent_id: str
    kind: Literal["idea", "challenge", "build", "reaction", "summary"]
    content: str
    to: str | None = None
    proposal_id: str | None = None


class IdeaPinned(EventBase):
    type: Literal["idea_pinned"] = "idea_pinned"
    room_id: str
    proposal_id: str
    author_id: str
    text: str


class UpvoteApplied(EventBase):
    type: Literal["upvote_applied"] = "upvote_applied"
    room_id: str
    proposal_id: str
    voter_id: str
    new_score: int


class AgentKnockedOut(EventBase):
    type: Literal["agent_knocked_out"] = "agent_knocked_out"
    room_id: str
    agent_id: str
    by_agent_id: str
    reason: str


class AgentRevived(EventBase):
    type: Literal["agent_revived"] = "agent_revived"
    room_id: str
    agent_id: str


class RoomConcluded(EventBase):
    type: Literal["room_concluded"] = "room_concluded"
    room_id: str
    forced: bool


class QuorumStarted(EventBase):
    type: Literal["quorum_started"] = "quorum_started"
    member_ids: list[str]


class QuorumVoteCast(EventBase):
    type: Literal["quorum_vote_cast"] = "quorum_vote_cast"
    voter_id: str
    room_choice: str


class QuorumConcluded(EventBase):
    type: Literal["quorum_concluded"] = "quorum_concluded"
    winner_room_id: str
    winner_proposal_id: str | None
    tally: dict[str, int]
    closing_line: str


class ToolError(EventBase):
    type: Literal["tool_error"] = "tool_error"
    agent_id: str
    tool: str
    message: str


class SessionEnded(EventBase):
    type: Literal["session_ended"] = "session_ended"
    final_state: str


Event = Union[
    SessionStarted,
    RoomFormed,
    TurnStarted,
    MessageSent,
    IdeaPinned,
    UpvoteApplied,
    AgentKnockedOut,
    AgentRevived,
    RoomConcluded,
    QuorumStarted,
    QuorumVoteCast,
    QuorumConcluded,
    ToolError,
    SessionEnded,
]
