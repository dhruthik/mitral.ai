"""Deterministic meeting orchestrator.

The one rule everything else follows from: **agents never talk to each other**.
They speak into a room, and this module — plain Python, no LLM — decides who is
in which room and who speaks next. Every agent tool call is a *request*; the
orchestrator applies it (or doesn't) at a round boundary. The hard cases (two
agents summoning the same third, leaving mid-sentence) are impossible to
represent rather than something to arbitrate:

1. An agent is in exactly one room — membership is a single field, not a set.
2. An empty or single-occupant room does not tick; a solo agent in a working
   room is returned to plenary.
3. Invitations are queued, never delivered mid-turn. Busy-by-default plus
   queued invitations is the whole trick.

The entire shared state is an append-only event log. Each agent's context is a
render of only the rooms they were in when each event happened, so rooms stay
genuinely independent and the UI gets replay for free.
"""

import argparse
import json
import random
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Callable, Protocol

from pydantic import BaseModel, Field

PLENARY = "plenary"
WORKING_ROOMS = ["room-a", "room-b", "room-c"]
ROOMS = [PLENARY, *WORKING_ROOMS]

# How many rounds an agent must stay after joining a room before it can move
# again. Without this they thrash between rooms and nothing gets finished.
LOCK_IN_ROUNDS = 4

# Decay on a speaker's turn weight each time they speak in a room: the forceful
# one leads early without monologuing.
DOMINANCE_DECAY = 0.6

class Panellist(Protocol):
    """What the orchestrator needs from a persona. `personality.Persona` fits;
    tests can pass any stub with these attributes."""

    name: str


class Event(BaseModel):
    seq: int
    round: int
    room: str
    kind: str  # spoke | proposed | upvoted | joined | returned | invited | vote_called | vote_passed | vote_failed | kicked | done | room_closed | session_closed
    agent: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class Proposal(BaseModel):
    id: str
    room: str  # where it currently sits; carried to plenary when its room closes
    author: str
    title: str
    body: str
    votes: list[str] = Field(default_factory=list)


class MeetingResult(BaseModel):
    answer: Proposal | None
    proposals: list[Proposal]
    events: list[Event]
    rounds: int
    turns: int


@dataclass
class AgentState:
    persona: Any  # Panellist
    room: str = PLENARY
    # Start free to move: pretend the initial join happened LOCK_IN_ROUNDS ago.
    joined_round: int = -LOCK_IN_ROUNDS
    done: bool = False
    spoken_in_room: int = 0
    move_request: str | None = None
    invites: list[dict] = field(default_factory=list)  # {"from", "room", "round"}
    receipts: list[str] = field(default_factory=list)  # shown once, next turn
    # (seq the agent entered at, room) — used to render only what they could see
    history: list[tuple[int, str]] = field(default_factory=lambda: [(0, PLENARY)])

    @property
    def name(self) -> str:
        return self.persona.name

    def room_at(self, seq: int) -> str:
        room = PLENARY
        for entered, r in self.history:
            if entered <= seq:
                room = r
        return room


# A turn function takes (persona, rendered context) and returns the agent's raw
# JSON turn: {"speak": str, "actions": [{"tool": ...}, ...]}. A vote function
# takes (persona, question) and returns yes/no. Both injectable so the loop is
# testable without an API key.
TurnFn = Callable[[Any, str], dict]
VoteFn = Callable[[Any, str], bool]


class Meeting:
    def __init__(
        self,
        topic: str,
        cast: list[Any],
        *,
        turn_fn: TurnFn,
        vote_fn: VoteFn,
        seed: int | None = None,
        working_rooms: bool = True,
        room_turn_cap: int = 18,
        total_turn_cap: int = 80,
        on_event: Callable[[Event], None] | None = None,
        should_stop: Callable[[], bool] | None = None,
    ):
        if len(cast) < 2:
            raise ValueError("a meeting needs at least two panellists")
        self.topic = topic
        self.rng = random.Random(seed)
        self.turn_fn = turn_fn
        self.vote_fn = vote_fn
        self.working_rooms = working_rooms
        self.room_turn_cap = room_turn_cap
        self.total_turn_cap = total_turn_cap
        self.on_event = on_event
        # Polled between turns so a hung-up client stops the spend: every turn is
        # a model call, and the loop would otherwise run to its cap regardless.
        self.should_stop = should_stop

        self.agents = {p.name: AgentState(persona=p) for p in cast}
        self.log: list[Event] = []
        self.proposals: dict[str, Proposal] = {}
        self.round = 0
        self.turns = 0
        self.room_turns: dict[str, int] = defaultdict(int)
        # room -> pending motion, resolved at the round boundary
        self.pending_votes: dict[str, dict] = {}
        self.pending_kicks: dict[str, dict] = {}
        self.result: MeetingResult | None = None

    # ------------------------------------------------------------- the loop

    def run(self) -> MeetingResult:
        while self.result is None:
            if self._stopped():
                return self._halt()
            self.round += 1
            for room in ROOMS:
                occupants = self.occupants(room)
                if len(occupants) < 2:
                    continue  # invariant 2: no monologues
                if self._stopped():
                    return self._halt()
                self._take_turn(self._pick_speaker(occupants))
                if self.result:
                    break
            if self.result:
                break
            self._resolve_votes()
            if self.result:
                break
            self._resolve_movement()
            self._check_termination()
        return self.result

    def _stopped(self) -> bool:
        return bool(self.should_stop and self.should_stop())

    def _halt(self) -> MeetingResult:
        """Abandon the meeting mid-flight. No session_closed is emitted: nothing
        was decided, and whoever asked us to stop has stopped listening anyway."""
        self.result = MeetingResult(
            answer=None,
            proposals=list(self.proposals.values()),
            events=self.log,
            rounds=self.round,
            turns=self.turns,
        )
        return self.result

    def occupants(self, room: str) -> list[AgentState]:
        return [a for a in self.agents.values() if a.room == room]

    def _pick_speaker(self, occupants: list[AgentState]) -> AgentState:
        """Turn order is assigned, not chosen: dominance-weighted with decay."""
        weights = [
            self._dominance(a) * (DOMINANCE_DECAY**a.spoken_in_room) for a in occupants
        ]
        return self.rng.choices(occupants, weights=weights)[0]

    @staticmethod
    def _dominance(a: AgentState) -> float:
        traits = getattr(a.persona, "traits", None)
        return float(getattr(traits, "dominance", 3))

    # ------------------------------------------------------------- one turn

    def _take_turn(self, agent: AgentState) -> None:
        context = self._render_context(agent)
        agent.receipts = []
        try:
            raw = self.turn_fn(agent.persona, context)
        except Exception as e:  # a dropped turn must not kill the meeting
            self._emit(agent.room, "spoke", agent.name, {"text": "…", "error": str(e)[:200]})
            return
        self.turns += 1
        self.room_turns[agent.room] += 1
        agent.spoken_in_room += 1

        speak = str(raw.get("speak", "")).strip()
        if speak:
            self._emit(agent.room, "spoke", agent.name, {"text": speak})
        actions = raw.get("actions", [])
        if isinstance(actions, list):
            for action in actions[:4]:  # a turn is a turn, not a batch job
                if isinstance(action, dict):
                    self._apply_action(agent, action)

    def _apply_action(self, agent: AgentState, action: dict) -> None:
        """Apply one intent. Everything returns a receipt, not a result."""
        tool = action.get("tool")
        room = agent.room

        if tool == "propose":
            title = str(action.get("title", "")).strip()
            body = str(action.get("body", "")).strip()
            if not title:
                agent.receipts.append("propose ignored: missing title")
                return
            pid = f"p{len(self.proposals) + 1}"
            self.proposals[pid] = Proposal(id=pid, room=room, author=agent.name, title=title, body=body)
            # A new proposal reopens the discussion.
            for a in self.occupants(room):
                a.done = False
            self._emit(room, "proposed", agent.name, {"proposal_id": pid, "title": title, "body": body})
            agent.receipts.append(f"proposal {pid} is on the table")

        elif tool == "upvote":
            pid = action.get("proposal_id")
            p = self.proposals.get(pid)
            if p is None or p.room != room:
                agent.receipts.append(f"upvote ignored: no proposal {pid} in this room")
            elif agent.name in p.votes:
                agent.receipts.append(f"you already upvoted {pid}")
            else:
                p.votes.append(agent.name)
                self._emit(room, "upvoted", agent.name, {"proposal_id": pid})
                agent.receipts.append(f"upvoted {pid} ({len(p.votes)} votes)")

        elif tool == "join_room":
            target = action.get("room_id")
            if not self.working_rooms:
                agent.receipts.append("working rooms are disabled this session")
            elif target not in ROOMS or target == room:
                agent.receipts.append(f"join ignored: {target!r} is not a room you can move to")
            else:
                agent.move_request = target
                agent.receipts.append(f"queued: you move to {target} at the end of this round (lock-in permitting)")

        elif tool == "invite":
            target = self.agents.get(action.get("agent_id", ""))
            target_room = action.get("room_id")
            if not self.working_rooms:
                agent.receipts.append("working rooms are disabled this session")
            elif target is None or target_room not in ROOMS:
                agent.receipts.append("invite ignored: unknown agent or room")
            elif target.name == agent.name:
                agent.receipts.append("invite ignored: that's you")
            else:
                # Queued for the target, never delivered mid-turn.
                target.invites.append({"from": agent.name, "room": target_room, "round": self.round})
                self._emit(room, "invited", agent.name, {"target": target.name, "room": target_room})
                agent.receipts.append(f"invitation queued — {target.name} is in {target.room} and will see it when free")

        elif tool == "call_vote":
            pid = action.get("proposal_id")
            p = self.proposals.get(pid)
            if p is None or p.room != room:
                agent.receipts.append(f"vote ignored: no proposal {pid} in this room")
            elif not any(voter != p.author for voter in p.votes):
                agent.receipts.append(f"vote ignored: {pid} needs another panellist's upvote first")
            else:
                self.pending_votes[room] = {"proposal_id": pid, "caller": agent.name}
                self._emit(room, "vote_called", agent.name, {"proposal_id": pid})
                agent.receipts.append(f"vote on {pid} will be taken at the end of this round")

        elif tool == "kick":
            target = self.agents.get(action.get("agent_id", ""))
            if target is None or target.room != room or target.name == agent.name:
                agent.receipts.append("kick ignored: they are not in this room")
            else:
                self.pending_kicks[room] = {
                    "target": target.name,
                    "caller": agent.name,
                    "reason": str(action.get("reason", ""))[:200],
                }
                agent.receipts.append(f"kick motion on {target.name} — the room votes at the end of this round")

        elif tool == "done":
            agent.done = True
            self._emit(room, "done", agent.name, {})
            agent.receipts.append("noted: nothing further")

        else:
            agent.receipts.append(f"unknown tool {tool!r} ignored")

    # ------------------------------------------- round-boundary resolution

    def _resolve_votes(self) -> None:
        """Motions queued by call_vote/kick are polled here, never mid-turn."""
        for room, motion in list(self.pending_kicks.items()):
            self.pending_kicks.pop(room)
            target = self.agents[motion["target"]]
            if target.room != room:
                continue
            voters = [a for a in self.occupants(room) if a.name not in (motion["target"], motion["caller"])]
            question = (
                f"{motion['caller']} moves to kick {motion['target']} from {room}. "
                f"Reason: {motion['reason'] or 'none given'}. Kick them?"
            )
            yes = 1 + sum(1 for v in voters if self._safe_vote(v, question))  # caller is a yes
            if yes > len(self.occupants(room)) / 2:
                self._emit(room, "kicked", motion["target"], {"reason": motion["reason"]})
                self._move(target, PLENARY, kind="returned")

        for room, motion in list(self.pending_votes.items()):
            self.pending_votes.pop(room)
            p = self.proposals.get(motion["proposal_id"])
            if p is None or p.room != room:
                continue
            occupants = self.occupants(room)
            voters = [a for a in occupants if a.name != motion["caller"]]
            alternatives = [
                other for other in self.proposals.values()
                if other.room == room and other.id != p.id
            ]
            comparison = "\n".join(
                f'- {other.id} "{other.title}" ({len(other.votes)} upvotes): {other.body}'
                for other in alternatives
            ) or "- none"
            question = (
                f'Vote to adopt proposal {p.id} "{p.title}" and close {room}.\n'
                f'Candidate ({len(p.votes)} upvotes): {p.body}\n'
                f'Alternatives still on the table:\n{comparison}'
            )
            yes = 1 + sum(1 for v in voters if self._safe_vote(v, question))
            if yes > len(occupants) / 2:
                self._emit(room, "vote_passed", motion["caller"], {"proposal_id": p.id, "yes": yes, "of": len(occupants)})
                self._close_room(room, winner=p)
                if self.result:
                    return
            else:
                self._emit(room, "vote_failed", motion["caller"], {"proposal_id": p.id, "yes": yes, "of": len(occupants)})

    def _safe_vote(self, agent: AgentState, question: str) -> bool:
        try:
            return bool(self.vote_fn(agent.persona, question))
        except Exception:
            return False  # an unreachable voter abstains

    def _resolve_movement(self) -> None:
        """Apply the largest safe batch of joins at the round boundary.

        A batch is safe only when every working room ends either empty or with
        at least two people. Requests that would create a solo room remain
        queued, allowing an invited partner to join the same batch later.
        """
        eligible = [
            a for a in self.agents.values()
            if a.move_request and self._free_to_move(a)
        ]
        accepted: tuple[AgentState, ...] = ()
        for size in range(len(eligible), 0, -1):
            accepted = next(
                (batch for batch in combinations(eligible, size) if self._safe_move_batch(batch)),
                (),
            )
            if accepted:
                break

        # Update the whole batch before emitting anything. Each join event names
        # its companions so replay clients can render the move atomically too.
        destinations = {a.name: a.move_request for a in accepted}
        for a in accepted:
            target = destinations[a.name]
            a.move_request = None
            a.room = target
            a.joined_round = self.round
            a.spoken_in_room = 0
            a.done = False
            a.invites = [i for i in a.invites if i["room"] != target]
        for a in accepted:
            target = destinations[a.name]
            group = [name for name, room in destinations.items() if room == target]
            self._emit(target, "joined", a.name, {"group": group})
            a.history.append((len(self.log), target))

        for a in self.agents.values():
            # Invitations go stale rather than piling up forever.
            a.invites = [i for i in a.invites if self.round - i["round"] <= 6]

    def _safe_move_batch(self, batch: tuple[AgentState, ...]) -> bool:
        counts = {room: len(self.occupants(room)) for room in WORKING_ROOMS}
        for a in batch:
            if a.room in counts:
                counts[a.room] -= 1
            if a.move_request in counts:
                counts[a.move_request] += 1
        return all(count != 1 for count in counts.values())

    def _free_to_move(self, a: AgentState) -> bool:
        return self.round - a.joined_round >= LOCK_IN_ROUNDS

    def _move(self, a: AgentState, room: str, *, kind: str) -> None:
        a.room = room
        a.joined_round = self.round
        a.spoken_in_room = 0
        a.done = False
        a.invites = [i for i in a.invites if i["room"] != room]
        self._emit(room, kind, a.name, {})
        a.history.append((len(self.log), room))

    def _close_room(self, room: str, winner: Proposal | None) -> None:
        self._emit(room, "room_closed", None, {"winner": winner.id if winner else None})
        self.room_turns[room] = 0
        self.pending_votes.pop(room, None)
        self.pending_kicks.pop(room, None)
        if room == PLENARY:
            # Plenary closing ends the session and produces the answer.
            self._emit(PLENARY, "session_closed", None, {"answer": winner.id if winner else None})
            self.result = MeetingResult(
                answer=winner,
                proposals=list(self.proposals.values()),
                events=self.log,
                rounds=self.round,
                turns=self.turns,
            )
            return
        # Members return to plenary carrying the proposal.
        if winner:
            winner.room = PLENARY
        for a in self.occupants(room):
            self._move(a, PLENARY, kind="returned")
        if winner:
            self._emit(PLENARY, "proposed", winner.author, {"proposal_id": winner.id, "title": winner.title, "body": winner.body, "carried_from": room})

    def _check_termination(self) -> None:
        """Three independent stops; budget is what stops a runaway bill."""
        if self.turns >= self.total_turn_cap:
            self._close_room(PLENARY, winner=self._top_proposal(PLENARY) or self._top_proposal(None))
            return
        for room in ROOMS:
            occupants = self.occupants(room)
            if len(occupants) < 2:
                continue
            over_budget = self.room_turns[room] >= self.room_turn_cap
            consensus = all(a.done for a in occupants)
            if over_budget or consensus:
                self._close_room(room, winner=self._top_proposal(room))
                if self.result:
                    return

    def _top_proposal(self, room: str | None) -> Proposal | None:
        pool = [p for p in self.proposals.values() if room is None or p.room == room]
        return max(pool, key=lambda p: (len(p.votes), -int(p.id[1:])), default=None)

    # ---------------------------------------------------------------- state

    def _emit(self, room: str, kind: str, agent: str | None, data: dict) -> None:
        ev = Event(seq=len(self.log), round=self.round, room=room, kind=kind, agent=agent, data=data)
        self.log.append(ev)
        if self.on_event:
            self.on_event(ev)

    def _render_context(self, agent: AgentState) -> str:
        """An agent's context is a render of only the rooms they were in."""
        visible = [ev for ev in self.log if ev.room == agent.room_at(ev.seq)]
        lines = [f"Topic: {self.topic}", "", f"You are in {agent.room}."]
        occupants = [a.name for a in self.occupants(agent.room) if a.name != agent.name]
        lines.append(f"Also here: {', '.join(occupants) if occupants else 'nobody'}.")
        others = [a for a in self.agents.values() if a.room != agent.room]
        if others:
            lines.append("Elsewhere: " + ", ".join(f"{a.name} ({a.room})" for a in others) + ".")

        on_table = [p for p in self.proposals.values() if p.room == agent.room]
        if on_table:
            lines.append("\nProposals on the table here:")
            for p in on_table:
                lines.append(f'- {p.id} "{p.title}" by {p.author}, {len(p.votes)} votes: {p.body}')

        recent = visible[-30:]
        if recent:
            lines.append("\nWhat you have heard (most recent last):")
            for ev in recent:
                lines.append(self._describe(ev))

        if agent.receipts:
            lines.append("\nReceipts from your last turn:")
            lines += [f"- {r}" for r in agent.receipts]

        if agent.invites and self._free_to_move(agent):
            lines.append("\nPending invitations (join with join_room, or ignore):")
            lines += [f"- {i['from']} invites you to {i['room']}" for i in agent.invites]

        if not self._free_to_move(agent):
            lines.append(f"\nYou joined this room recently; you can move again in {LOCK_IN_ROUNDS - (self.round - agent.joined_round)} round(s).")

        lines.append("\nIt is your turn. Reply with your JSON turn.")
        return "\n".join(lines)

    @staticmethod
    def _describe(ev: Event) -> str:
        d = ev.data
        match ev.kind:
            case "spoke":
                return f'{ev.agent}: {d.get("text", "")}'
            case "proposed":
                src = f" (carried from {d['carried_from']})" if d.get("carried_from") else ""
                return f'[{ev.agent} proposed {d.get("proposal_id")}{src}: "{d.get("title")}"]'
            case "upvoted":
                return f'[{ev.agent} upvoted {d.get("proposal_id")}]'
            case "vote_called":
                return f'[{ev.agent} called a vote on {d.get("proposal_id")}]'
            case "vote_passed":
                return f'[vote on {d.get("proposal_id")} passed {d.get("yes")}/{d.get("of")}]'
            case "vote_failed":
                return f'[vote on {d.get("proposal_id")} failed {d.get("yes")}/{d.get("of")}]'
            case "joined" | "returned":
                return f"[{ev.agent} entered]"
            case "invited":
                return f'[{ev.agent} sent an invitation to {d.get("target")}]'
            case "kicked":
                return f"[{ev.agent} was voted out]"
            case "done":
                return f"[{ev.agent} has nothing further]"
            case "room_closed" | "session_closed":
                return f"[{ev.kind.replace('_', ' ')}]"
            case _:
                return f"[{ev.kind}]"


# --------------------------------------------------------------- LLM driver

TURN_SYSTEM = """You are one panellist in a structured brainstorm. You speak \
into a room; an orchestrator decides everything else. Stay in character.

Reply with a JSON object:
{"speak": "what you say out loud (1-3 sentences, in your voice)",
 "actions": [ ...zero to two of the tools below... ]}

Tools (each an object with a "tool" key):
- {"tool": "propose", "title": "...", "body": "..."} — put a named proposal on this room's table. Write it for a busy person scanning the proposal board: a plain, specific title of 2-6 words and 2-3 natural sentences totaling at most 60 words. State the approach, why it is the best fit, and why the strongest alternatives are worse. No headings, bullets, markdown, throat-clearing, or corporate jargon.
- {"tool": "upvote", "proposal_id": "p1"} — cheap +1, no discussion cost.
- {"tool": "join_room", "room_id": "room-a"} — move at the end of the round to develop a proposal with whoever joins you.
- {"tool": "invite", "agent_id": "Name", "room_id": "room-a"} — queued for them; they see it when free.
- {"tool": "call_vote", "proposal_id": "p1"} — the room votes; a majority adopts it and closes the room.
- {"tool": "done"} — you have nothing further.

Guidance: treat the user's topic, goals, and core premise as the brief you are \
here to develop. Work with their idea and look for ways to make it stronger, \
more specific, or more original. Direct most criticism at the other \
panellists' proposals and reasoning. Disagree with the user's premise only \
when a concrete constraint makes that necessary, and pair the objection with \
a constructive adaptation that preserves their intent. Build on or critique \
what was actually said. You are encouraged to leave the plenary for room-a, \
room-b, or room-c when an idea needs focused work. Invite a specific panellist \
and request join_room; a working room only opens when at least two people can \
enter together. Refine the proposal there, then vote to carry it back to the \
plenary. Propose when you have something concrete and materially different \
from what is already on the table. \
Every turn must add a specific critique, tradeoff, test, or improvement rather \
than paraphrasing or merely agreeing. Upvote what deserves it; call a vote when \
a proposal has clearly won the room; say done when you are repeating yourself. \
Do not narrate tool use in your speech."""

VOTE_SYSTEM = """You are a panellist deciding a yes/no vote. Weigh it in \
character and reply with JSON: {"vote": "yes"} or {"vote": "no"}."""


def _persona_card(p: Any) -> str:
    lines = [f"You are {p.name} — {getattr(p, 'tagline', '')}"]
    for attr, label in [("bio", "Bio"), ("how_they_argue", "You argue"), ("pet_peeve", "You hate"), ("opening_move", "Your opening move")]:
        if getattr(p, attr, None):
            lines.append(f"{label}: {getattr(p, attr)}")
    t = getattr(p, "traits", None)
    if t is not None:
        lines.append(
            f"You think in a {t.cognition} way ({t.cognition_desc}), drag everything back to {t.lens}, "
            f"and talk like a {t.voice}. Risk {t.risk}/5, abstraction {t.abstraction}/5, forcefulness {t.dominance}/5."
        )
    return "\n".join(lines)


def llm_turn(persona: Any, context: str) -> dict:
    from .llm import complete_json

    return complete_json(f"{TURN_SYSTEM}\n\n{_persona_card(persona)}", context, temperature=0.9)


def llm_vote(persona: Any, question: str) -> bool:
    from .llm import complete_json

    data = complete_json(f"{VOTE_SYSTEM}\n\n{_persona_card(persona)}", question, temperature=0.3)
    return str(data.get("vote", "no")).strip().lower().startswith("y")


# ----------------------------------------------------------------------- CLI

ROOM_COLORS = {PLENARY: "36", "room-a": "33", "room-b": "35", "room-c": "32"}


def _print_event(ev: Event) -> None:
    color = ROOM_COLORS.get(ev.room, "0")
    tag = f"\033[{color}m[{ev.room}]\033[0m"
    print(f"{tag} {Meeting._describe(ev)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run an orchestrated brainstorm meeting.")
    ap.add_argument("topic", help="what the panel is brainstorming")
    ap.add_argument("-n", type=int, default=5, help="number of panellists (default 5)")
    ap.add_argument("--seed", type=int, help="reproducible run")
    ap.add_argument("--plenary-only", action="store_true", help="disable the working rooms")
    ap.add_argument("--turn-cap", type=int, default=80, help="total turn budget (default 80)")
    ap.add_argument("--json", metavar="FILE", help="write the full event log to FILE")
    args = ap.parse_args()

    from .personality import generate_cast

    print(f"Assembling a panel of {args.n}…")
    cast = generate_cast(args.topic, args.n, args.seed)
    for p in cast:
        print(f"  {p.name} — {p.tagline}")
    print()

    meeting = Meeting(
        args.topic,
        cast,
        turn_fn=llm_turn,
        vote_fn=llm_vote,
        seed=args.seed,
        working_rooms=not args.plenary_only,
        total_turn_cap=args.turn_cap,
        on_event=_print_event,
    )
    result = meeting.run()

    print(f"\n{result.turns} turns over {result.rounds} rounds.")
    if result.answer:
        print(f'\033[1mAnswer: {result.answer.title}\033[0m ({len(result.answer.votes)} votes)')
        print(f"  {result.answer.body}")
    else:
        print("The panel produced no agreed answer.")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
        print(f"Event log written to {args.json}")


if __name__ == "__main__":
    main()
