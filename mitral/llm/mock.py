import random
from typing import Callable, Union

from mitral.llm.base import LLMClient, ToolCallResponse
from mitral.llm.templates import TEMPLATES, fill, gen_seed, keywords
from mitral.models.agent import AgentRuntime
from mitral.models.session import Room, Session

ScriptEntry = Union[ToolCallResponse, Callable[[Session], ToolCallResponse]]


class MockLLMClient(LLMClient):
    """Deterministic-ish, zero-API-key LLM stand-in. By default it generates
    stance-templated dialogue mirroring the UI team's mocked prototype. Tests
    can force specific turns via `script`, keyed by (agent_id, room_id, call
    index for that agent+room pair) — the index lets a test script only the
    interesting turns without predicting exact round numbers."""

    def __init__(self, script: dict[tuple[str, str, int], ScriptEntry] | None = None, seed: int | None = None):
        self.script = script or {}
        self.rng = random.Random(seed)
        self._call_counts: dict[tuple[str, str], int] = {}
        self._last_move: dict[str, str] = {}
        self._last_idea_by: dict[str, str] = {}

    async def get_tool_call(
        self,
        *,
        agent: AgentRuntime,
        session: Session,
        room: Room,
        allowed_tools: list[str],
        context: str = "",
    ) -> ToolCallResponse:
        key_base = (agent.agent_id, room.id)
        idx = self._call_counts.get(key_base, 0)
        self._call_counts[key_base] = idx + 1

        scripted = self.script.get((agent.agent_id, room.id, idx))
        if scripted is not None:
            return scripted(session) if callable(scripted) else scripted

        if "cast_vote" in allowed_tools and room.id == "q":
            return self._auto_vote(agent, session)

        return self._auto_speak(agent, session, room)

    def _auto_vote(self, agent: AgentRuntime, session: Session) -> ToolCallResponse:
        home = "room0" if agent.agent_id in session.rooms["room0"].member_ids else "room1"
        other = "room1" if home == "room0" else "room0"
        choice = home if self.rng.random() < 0.72 else other
        return ToolCallResponse(tool_name="cast_vote", arguments={"room_choice": choice})

    def _auto_speak(self, agent: AgentRuntime, session: Session, room: Room) -> ToolCallResponse:
        stance = agent.personality.stance.value
        kws = keywords(session.idea)
        slots = {"topic": session.idea, "room": room.title}

        if room.round == 0:
            text = fill(self.rng.choice(TEMPLATES["opener"][stance]), slots)
            self._last_move[room.id] = "opener"
            return ToolCallResponse(tool_name="speak", arguments={"content": text, "kind": "reaction"})

        last_move = self._last_move.get(room.id, "opener")
        prev_idea_by = self._last_idea_by.get(room.id)
        seed = gen_seed(kws, self.rng)
        prev_name = (
            session.agents[prev_idea_by].personality.name if prev_idea_by else agent.personality.name
        )
        fill_slots = {**slots, "seed": seed, "prevName": prev_name}

        if last_move == "idea" and prev_idea_by and TEMPLATES["challenge"].get(stance) and self.rng.random() < 0.45:
            move = "challenge"
        elif last_move == "idea":
            move = "build" if self.rng.random() < 0.5 else "reaction"
        else:
            move = "idea" if self.rng.random() < 0.7 else "reaction"

        if move == "idea":
            text = fill(self.rng.choice(TEMPLATES["idea"][stance]), fill_slots)
            self._last_move[room.id] = "idea"
            self._last_idea_by[room.id] = agent.agent_id
            return ToolCallResponse(tool_name="speak", arguments={"content": text, "kind": "idea", "as_idea": True})
        if move == "challenge":
            text = fill(self.rng.choice(TEMPLATES["challenge"][stance]), fill_slots)
            self._last_move[room.id] = "challenge"
            to = prev_idea_by if prev_idea_by != agent.agent_id else None
            return ToolCallResponse(tool_name="speak", arguments={"content": text, "kind": "challenge", "to": to})
        if move == "build" and TEMPLATES["build"].get(stance):
            text = fill(self.rng.choice(TEMPLATES["build"][stance]), fill_slots)
            self._last_move[room.id] = "idea"
            self._last_idea_by[room.id] = agent.agent_id
            to = prev_idea_by if prev_idea_by != agent.agent_id else None
            return ToolCallResponse(
                tool_name="speak", arguments={"content": text, "kind": "build", "to": to, "as_idea": True}
            )

        text = fill(self.rng.choice(TEMPLATES["reaction"][stance]), fill_slots)
        self._last_move[room.id] = "reaction"
        return ToolCallResponse(tool_name="speak", arguments={"content": text, "kind": "reaction"})

    async def pitch_line(self, *, agent: AgentRuntime, session: Session, room: Room) -> str:
        proposal = session.proposals.get(room.best_proposal_id) if room.best_proposal_id else None
        best = proposal.text if proposal else "a bold new direction"
        stance = agent.personality.stance.value
        tpl = self.rng.choice(TEMPLATES["pitch"].get(stance, TEMPLATES["pitch"]["pragmatist"]))
        return fill(tpl, {"room": room.title, "best": best})

    async def closing_line(
        self, *, agent: AgentRuntime, session: Session, room: Room, votes: dict[str, int]
    ) -> str:
        proposal = session.proposals.get(room.best_proposal_id) if room.best_proposal_id else None
        winner = proposal.text if proposal else "the winning idea"
        v_sorted = sorted(votes.values(), reverse=True)
        votes_str = f"{v_sorted[0]}–{v_sorted[1] if len(v_sorted) > 1 else 0}"
        return fill(TEMPLATES["closer"][0], {"topic": session.idea, "winner": winner, "votes": votes_str})
