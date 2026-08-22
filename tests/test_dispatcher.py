import pytest

from mitral.llm.base import ToolCallResponse
from mitral.tools.dispatcher import ToolValidationError, dispatch


def test_speak_pins_idea_and_recomputes_best(session):
    room = session.rooms["room0"]
    agent = session.agents["d"]
    call = ToolCallResponse(tool_name="speak", arguments={"content": "a night market", "kind": "idea", "as_idea": True})

    events = dispatch(session, room, agent, call, round_no=0)

    assert [e.type for e in events] == ["message_sent", "idea_pinned"]
    assert len(session.proposals) == 1
    proposal = next(iter(session.proposals.values()))
    assert proposal.author_id == "d"
    assert room.best_proposal_id == proposal.id
    assert agent.last_action.tool == "speak"


def test_speak_to_must_be_room_member(session):
    room = session.rooms["room0"]  # members: d, a, w
    agent = session.agents["d"]
    call = ToolCallResponse(tool_name="speak", arguments={"content": "hey", "kind": "reaction", "to": "s"})

    with pytest.raises(ToolValidationError):
        dispatch(session, room, agent, call, round_no=0)


def test_upvote_rejects_self_upvote_and_double_upvote(session):
    room = session.rooms["room0"]
    author = session.agents["d"]
    dispatch(
        session, room, author,
        ToolCallResponse(tool_name="speak", arguments={"content": "idea", "kind": "idea", "as_idea": True}),
        round_no=0,
    )
    proposal_id = next(iter(session.proposals))

    with pytest.raises(ToolValidationError):
        dispatch(session, room, author, ToolCallResponse(tool_name="upvote_idea", arguments={"proposal_id": proposal_id}), round_no=1)

    voter = session.agents["a"]
    events = dispatch(session, room, voter, ToolCallResponse(tool_name="upvote_idea", arguments={"proposal_id": proposal_id}), round_no=1)
    assert events[0].type == "upvote_applied"
    assert session.proposals[proposal_id].score == 1

    with pytest.raises(ToolValidationError):
        dispatch(session, room, voter, ToolCallResponse(tool_name="upvote_idea", arguments={"proposal_id": proposal_id}), round_no=2)


def test_knock_out_rejects_self_and_non_member_and_double_ko(session):
    room = session.rooms["room0"]
    agent = session.agents["d"]

    with pytest.raises(ToolValidationError):
        dispatch(session, room, agent, ToolCallResponse(tool_name="knock_out", arguments={"target_id": "d"}), round_no=0)

    with pytest.raises(ToolValidationError):
        dispatch(session, room, agent, ToolCallResponse(tool_name="knock_out", arguments={"target_id": "s"}), round_no=0)

    events = dispatch(session, room, agent, ToolCallResponse(tool_name="knock_out", arguments={"target_id": "a"}), round_no=0)
    assert events[0].type == "agent_knocked_out"
    assert session.agents["a"].status == "knocked_out"

    with pytest.raises(ToolValidationError):
        dispatch(session, room, agent, ToolCallResponse(tool_name="knock_out", arguments={"target_id": "a"}), round_no=1)


def test_unknown_tool_and_bad_enum_rejected(session):
    room = session.rooms["room0"]
    agent = session.agents["d"]

    with pytest.raises(ToolValidationError):
        dispatch(session, room, agent, ToolCallResponse(tool_name="teleport", arguments={}), round_no=0)

    with pytest.raises(ToolValidationError):
        dispatch(session, room, agent, ToolCallResponse(tool_name="speak", arguments={"content": "x", "kind": "not-a-kind"}), round_no=0)
