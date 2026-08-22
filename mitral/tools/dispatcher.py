import uuid
from typing import Any

from mitral.llm.base import ToolCallResponse
from mitral.models.agent import ActionRecord, AgentRuntime
from mitral.models.events import (
    AgentKnockedOut,
    Event,
    IdeaPinned,
    MessageSent,
    QuorumVoteCast,
    UpvoteApplied,
)
from mitral.models.session import Proposal, Room, Session
from mitral.tools.definitions import TOOL_SCHEMAS


class ToolValidationError(Exception):
    pass


def validate_shape(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    schema = TOOL_SCHEMAS.get(tool_name)
    if schema is None:
        raise ToolValidationError(f"unknown tool '{tool_name}'")
    props = schema["parameters"].get("properties", {})
    required = schema["parameters"].get("required", [])
    for key in required:
        if key not in arguments:
            raise ToolValidationError(f"{tool_name} missing required '{key}'")
    for key, value in arguments.items():
        if key not in props:
            raise ToolValidationError(f"{tool_name} got unexpected argument '{key}'")
        enum = props[key].get("enum")
        if enum and value not in enum:
            raise ToolValidationError(f"{tool_name}.{key} must be one of {enum}, got {value!r}")
    return arguments


def _recompute_best(room: Room, session: Session) -> None:
    candidates = [p for p in session.proposals.values() if p.room_id == room.id]
    if not candidates:
        room.best_proposal_id = None
        return
    best = max(candidates, key=lambda p: p.score)
    room.best_proposal_id = best.id


def _handle_speak(session: Session, room: Room, agent: AgentRuntime, args: dict[str, Any]) -> list[Event]:
    content = args["content"]
    kind = args["kind"]
    to = args.get("to")
    as_idea = args.get("as_idea", False)

    if to is not None and to != "you":
        if to == agent.agent_id or to not in room.member_ids:
            raise ToolValidationError(f"speak.to '{to}' must be another member of {room.id}")

    proposal_id = None
    events: list[Event] = []
    if as_idea or kind == "idea":
        proposal_id = uuid.uuid4().hex
        session.proposals[proposal_id] = Proposal(
            id=proposal_id, room_id=room.id, author_id=agent.agent_id, text=content
        )
        _recompute_best(room, session)

    events.append(
        MessageSent(
            session_id=session.id,
            room_id=room.id,
            agent_id=agent.agent_id,
            kind=kind,
            content=content,
            to=to,
            proposal_id=proposal_id,
        )
    )
    if proposal_id is not None:
        events.append(
            IdeaPinned(
                session_id=session.id,
                room_id=room.id,
                proposal_id=proposal_id,
                author_id=agent.agent_id,
                text=content,
            )
        )
    return events


def _handle_upvote_idea(session: Session, room: Room, agent: AgentRuntime, args: dict[str, Any]) -> list[Event]:
    proposal_id = args["proposal_id"]
    proposal = session.proposals.get(proposal_id)
    if proposal is None or proposal.room_id != room.id:
        raise ToolValidationError(f"no proposal '{proposal_id}' in {room.id}")
    if proposal.author_id == agent.agent_id:
        raise ToolValidationError("cannot upvote your own idea")
    if agent.agent_id in proposal.upvoted_by:
        raise ToolValidationError("already upvoted this idea")

    proposal.upvoted_by.add(agent.agent_id)
    proposal.score += 1
    _recompute_best(room, session)
    return [
        UpvoteApplied(
            session_id=session.id,
            room_id=room.id,
            proposal_id=proposal_id,
            voter_id=agent.agent_id,
            new_score=proposal.score,
        )
    ]


def _handle_knock_out(session: Session, room: Room, agent: AgentRuntime, args: dict[str, Any]) -> list[Event]:
    target_id = args["target_id"]
    reason = args.get("reason", "")
    if target_id == agent.agent_id or target_id not in room.member_ids:
        raise ToolValidationError(f"knock_out.target_id '{target_id}' must be another member of {room.id}")
    target = session.agents[target_id]
    if target.status == "knocked_out":
        raise ToolValidationError(f"'{target_id}' is already knocked out")

    target.status = "knocked_out"
    return [
        AgentKnockedOut(
            session_id=session.id,
            room_id=room.id,
            agent_id=target_id,
            by_agent_id=agent.agent_id,
            reason=reason,
        )
    ]


def _handle_propose_wrap(session: Session, room: Room, agent: AgentRuntime, args: dict[str, Any]) -> list[Event]:
    return []


def _handle_cast_vote(session: Session, room: Room, agent: AgentRuntime, args: dict[str, Any]) -> list[Event]:
    room_choice = args["room_choice"]
    return [
        QuorumVoteCast(session_id=session.id, voter_id=agent.agent_id, room_choice=room_choice)
    ]


_HANDLERS = {
    "speak": _handle_speak,
    "upvote_idea": _handle_upvote_idea,
    "knock_out": _handle_knock_out,
    "propose_wrap": _handle_propose_wrap,
    "cast_vote": _handle_cast_vote,
}


def dispatch(
    session: Session, room: Room, agent: AgentRuntime, call: ToolCallResponse, round_no: int
) -> list[Event]:
    args = validate_shape(call.tool_name, call.arguments)
    handler = _HANDLERS[call.tool_name]
    events = handler(session, room, agent, args)
    agent.last_action = ActionRecord(tool=call.tool_name, payload=args, round=round_no)
    return events
