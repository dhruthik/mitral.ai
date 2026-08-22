import random
from asyncio import gather
from typing import Any, Protocol

from mitral.engine import tally
from mitral.engine.turn_taking import next_speaker
from mitral.llm.base import LLMClient
from mitral.models.events import (
    AgentRevived,
    Event,
    MessageSent,
    QuorumConcluded,
    QuorumStarted,
    RoomConcluded,
    RoomFormed,
    SessionEnded,
    SessionStarted,
    ToolError,
    TurnStarted,
)
from mitral.models.session import QuorumResult, Room, Session, SessionState, RoomState
from mitral.tools.dispatcher import ToolValidationError, dispatch

BREAKOUT_TOOLS = ["speak", "upvote_idea", "knock_out", "propose_wrap"]


class EventSink(Protocol):
    def publish(self, event: Any) -> None: ...


class Orchestrator:
    """Runs one brainstorming Session end to end: both breakout rooms
    concurrently, then a sequential Quorum convergence. See the design plan
    for why rooms run concurrently (they're genuinely parallel breakout
    conversations) while the Quorum is sequential (one shared vote)."""

    def __init__(self, session: Session, llm: LLMClient, bus: EventSink, rng: random.Random | None = None):
        self.session = session
        self.llm = llm
        self.bus = bus
        self.rng = rng or random.Random()

    async def run(self) -> None:
        s = self.session
        s.state = SessionState.BREAKOUT
        self.bus.publish(
            SessionStarted(
                session_id=s.id,
                idea=s.idea,
                roster=[
                    {
                        "id": a.agent_id,
                        "name": a.personality.name,
                        "stance": a.personality.stance.value,
                        "label": a.personality.label,
                        "color": a.personality.color,
                        "room_id": a.room_id,
                    }
                    for a in s.agents.values()
                ],
                max_rounds_per_room=s.max_rounds_per_room,
            )
        )
        for room in (s.rooms["room0"], s.rooms["room1"]):
            self.bus.publish(
                RoomFormed(
                    session_id=s.id,
                    room_id=room.id,
                    title=room.title,
                    tag=room.tag,
                    color=room.color,
                    member_ids=room.member_ids,
                )
            )

        await gather(self._run_room(s.rooms["room0"]), self._run_room(s.rooms["room1"]))
        await self._run_quorum()

        s.state = SessionState.CONCLUDED
        self.bus.publish(SessionEnded(session_id=s.id, final_state=s.state.value))

    async def _run_room(self, room: Room) -> None:
        s = self.session
        forced = False
        while True:
            if room.round >= s.max_rounds_per_room:
                forced = True
                break
            if tally.wrap_ready(room, s):
                break

            speaker_id = next_speaker(room)
            agent = s.agents[speaker_id]
            if agent.status == "knocked_out":
                agent.status = "active"
                self.bus.publish(AgentRevived(session_id=s.id, room_id=room.id, agent_id=agent.agent_id))

            self.bus.publish(
                TurnStarted(session_id=s.id, room_id=room.id, agent_id=agent.agent_id, round=room.round)
            )
            events = await self._get_and_dispatch(room, agent, BREAKOUT_TOOLS)
            for ev in events:
                self.bus.publish(ev)
                if isinstance(ev, MessageSent) and ev.to not in (None, "you"):
                    room.forced_next = ev.to
            room.round += 1

        room.state = RoomState.CONCLUDED
        self.bus.publish(RoomConcluded(session_id=s.id, room_id=room.id, forced=forced))

    async def _get_and_dispatch(self, room: Room, agent, allowed_tools: list[str]) -> list[Event]:
        s = self.session
        error_ctx = ""
        for _ in range(2):
            call = await self.llm.get_tool_call(
                agent=agent, session=s, room=room, allowed_tools=allowed_tools, context=error_ctx
            )
            try:
                return dispatch(s, room, agent, call, room.round)
            except ToolValidationError as e:
                self.bus.publish(
                    ToolError(session_id=s.id, agent_id=agent.agent_id, tool=call.tool_name, message=str(e))
                )
                error_ctx = f"Your last action was invalid: {e}. Try a different one."
        return []

    def _pick_delegate(self, room: Room) -> str:
        for agent_id in room.member_ids:
            if self.session.agents[agent_id].status != "knocked_out":
                return agent_id
        return room.member_ids[0]

    async def _run_quorum(self) -> None:
        s = self.session
        s.state = SessionState.QUORUM
        quorum_room = s.rooms["q"]
        all_ids = list(s.agents.keys())
        self.bus.publish(QuorumStarted(session_id=s.id, member_ids=all_ids))

        r0, r1 = s.rooms["room0"], s.rooms["room1"]
        delegate0, delegate1 = self._pick_delegate(r0), self._pick_delegate(r1)

        for delegate, room in ((delegate0, r0), (delegate1, r1)):
            pitch = await self.llm.pitch_line(agent=s.agents[delegate], session=s, room=room)
            self.bus.publish(
                MessageSent(
                    session_id=s.id, room_id="q", agent_id=delegate, kind="summary", content=pitch, to="you"
                )
            )

        others = [a for a in all_ids if a not in (delegate0, delegate1)]
        if others:
            reactor = self.rng.choice(others)
            home_room = r0 if reactor in r0.member_ids else r1
            reaction = await self.llm.pitch_line(agent=s.agents[reactor], session=s, room=home_room)
            self.bus.publish(
                MessageSent(session_id=s.id, room_id="q", agent_id=reactor, kind="reaction", content=reaction)
            )

        for agent_id in all_ids:
            events = await self._get_and_dispatch(quorum_room, s.agents[agent_id], ["cast_vote"])
            for ev in events:
                self.bus.publish(ev)

        tally_result = tally.quorum_tally(s)
        winner_room_id = "room0" if tally_result.get("room0", 0) >= tally_result.get("room1", 0) else "room1"
        winner_room = s.rooms[winner_room_id]
        winner_delegate = delegate0 if winner_room_id == "room0" else delegate1

        closing = await self.llm.closing_line(
            agent=s.agents[winner_delegate], session=s, room=winner_room, votes=tally_result
        )
        s.result = QuorumResult(
            winner_room_id=winner_room_id,
            winner_proposal_id=winner_room.best_proposal_id,
            tally=tally_result,
            closing_line=closing,
        )
        self.bus.publish(
            MessageSent(
                session_id=s.id, room_id="q", agent_id=winner_delegate, kind="summary", content=closing, to="you"
            )
        )
        self.bus.publish(
            QuorumConcluded(
                session_id=s.id,
                winner_room_id=winner_room_id,
                winner_proposal_id=winner_room.best_proposal_id,
                tally=tally_result,
                closing_line=closing,
            )
        )
