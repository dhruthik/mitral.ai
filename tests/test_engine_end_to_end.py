import asyncio

from mitral.engine.factory import new_session
from mitral.engine.orchestrator import Orchestrator
from mitral.llm.base import ToolCallResponse
from mitral.llm.mock import MockLLMClient
from mitral.server.event_bus import SessionEventBus

VOTE_ROOM0 = ToolCallResponse(tool_name="cast_vote", arguments={"room_choice": "room0"})


def _speak(content, kind="reaction", **extra):
    return ToolCallResponse(tool_name="speak", arguments={"content": content, "kind": kind, **extra})


def test_full_meeting_kick_upvote_wrap_and_quorum(session):
    # room0 = d, a, w; room1 = s, p (see conftest)
    script = {
        ("d", "room0", 0): _speak("here's an idea", kind="idea", as_idea=True),
        ("d", "room0", 1): _speak("just chatting"),
        ("a", "room0", 1): ToolCallResponse(tool_name="propose_wrap", arguments={}),
        ("w", "room0", 0): ToolCallResponse(tool_name="knock_out", arguments={"target_id": "a"}),
        ("w", "room0", 1): ToolCallResponse(tool_name="propose_wrap", arguments={}),
        # d's third turn (after being called for idea, reaction) proposes wrap -> quorum reached (3/3)
        ("d", "room0", 2): ToolCallResponse(tool_name="propose_wrap", arguments={}),
    }

    # upvote needs the real proposal id, only known once "d" has spoken; use a callable entry.
    def upvote_first_room0_idea(sess):
        proposal_id = next(pid for pid, p in sess.proposals.items() if p.room_id == "room0")
        return ToolCallResponse(tool_name="upvote_idea", arguments={"proposal_id": proposal_id})

    script[("a", "room0", 0)] = upvote_first_room0_idea

    for agent_id in ("d", "a", "w", "s", "p"):
        script[(agent_id, "q", 0)] = VOTE_ROOM0

    llm = MockLLMClient(script=script, seed=7)
    bus = SessionEventBus()
    orchestrator = Orchestrator(session, llm, bus)

    asyncio.run(orchestrator.run())

    types = [e.type for e in bus.log]

    assert types[0] == "session_started"
    assert types.count("room_formed") == 2
    assert types[-1] == "session_ended"

    assert "agent_knocked_out" in types
    ko_index = types.index("agent_knocked_out")
    revived = [e for e in bus.log if e.type == "agent_revived" and e.agent_id == "a"]
    assert revived, "agent 'a' should auto-revive before their next turn"
    assert bus.log.index(revived[0]) > ko_index

    upvote_events = [e for e in bus.log if e.type == "upvote_applied"]
    assert len(upvote_events) == 1
    assert upvote_events[0].new_score == 1

    room0_concluded = next(e for e in bus.log if e.type == "room_concluded" and e.room_id == "room0")
    assert room0_concluded.forced is False

    room1_concluded = next(e for e in bus.log if e.type == "room_concluded" and e.room_id == "room1")
    assert room1_concluded.forced is True  # ran to the max_rounds safety cap, nobody proposed wrap

    assert types.index("quorum_started") > types.index("room_concluded")

    quorum_concluded = next(e for e in bus.log if e.type == "quorum_concluded")
    assert quorum_concluded.winner_room_id == "room0"
    assert quorum_concluded.tally == {"room0": 5, "room1": 0}

    room0_proposals = [p for p in session.proposals.values() if p.room_id == "room0"]
    assert len(room0_proposals) == 1
    assert quorum_concluded.winner_proposal_id == room0_proposals[0].id

    assert session.state.value == "concluded"


def test_room_hits_safety_cap_when_nobody_proposes_wrap(cast, rng):
    session = new_session("a topic", cast=cast, rng=rng, session_id="sess-cap")
    session.max_rounds_per_room = 3

    llm = MockLLMClient(seed=3)  # no script: pure auto-speak, nobody ever proposes wrap
    bus = SessionEventBus()
    orchestrator = Orchestrator(session, llm, bus)

    asyncio.run(orchestrator.run())

    for room_id in ("room0", "room1"):
        concluded = next(e for e in bus.log if e.type == "room_concluded" and e.room_id == room_id)
        assert concluded.forced is True
        assert session.rooms[room_id].round == 3

    assert session.state.value == "concluded"
    assert bus.log[-1].type == "session_ended"
