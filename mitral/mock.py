"""Offline drivers for the meeting orchestrator.

Zero API calls: a template cast and a reactive turn policy that exercise the
whole meeting loop — proposals, upvotes, a room split with an invitation, a
carried proposal, and a closing vote — so the UI has something real to play
back before any LLM key exists. The orchestrator cannot tell the difference:
it sees the same tools either way.
"""

import random
import re

from .personality import Persona, Traits, sample_traits

NAMES = [
    "Nova", "Rex", "June", "Priya", "Zed", "Lumi", "Otto", "Mara",
    "Silas", "Wren", "Kofi", "Ida",
]

ADJECTIVES = ["tiny", "members-only", "after-hours", "pay-what-you-want", "invite-only", "seasonal", "roaming", "open-source"]
FORMATS = ["club", "ritual", "passport", "pop-up", "subscription", "swap meet", "residency", "league"]
VERBS = ["rewards", "connects", "gamifies", "documents", "celebrates", "simplifies"]
AUDIENCES = ["regulars", "night owls", "first-timers", "neighbors", "commuters", "skeptics"]

BANTER = [
    "Building on that — the {lens} angle is what makes it defensible.",
    "I keep coming back to {kw}. That's where the value is.",
    "Devil's advocate for a second: would {aud} actually care?",
    "In {lens} they solved exactly this. Same shape, different costume.",
    "Cheapest test: fake it for a weekend and count who shows up.",
    "I'd rather ship the boring version of this next week.",
]


ANSWERS = [
    "\"{said}\" only matters if {aud} come back a second time. Do they?",
    "The {how} read of \"{said}\": that's the interesting half, the rest is decoration.",
    "I'd push back on \"{said}\" — it assumes someone here has done this before.",
    "Cheapest test of \"{said}\": fake it for a weekend and count who shows up.",
    "Agreed on \"{said}\", but say the number out loud before we build anything.",
    "\"{said}\" is the part I'd keep. Throw out everything else about {kw}.",
]


def _kw(topic: str, rng: random.Random) -> str:
    words = re.findall(r"[a-z']{4,}", topic.lower()) or ["idea"]
    return rng.choice(words)


def _echo(message: str) -> str:
    """The longest real word in what the human said, to quote back at them.

    There is no parser here, and echoing "what" or "when" reads like the panel
    misheard you; the longest word is nearly always the one that carries it.
    """
    words = re.findall(r"[A-Za-z'-]{4,}", message)
    return max(words, key=len) if words else "that"


def mock_cast(topic: str, n: int = 4, seed: int | None = None, mode: str = "wild") -> list[Persona]:
    """A cast with real sampled traits and template prose. No API calls."""
    rng = random.Random(seed)
    names = rng.sample(NAMES, n)
    cast = []
    for name, t in zip(names, sample_traits(n, rng, mode)):
        # Demo mode has no model to write the free-text field, so derive a
        # topic-specific lens rather than restoring a hidden fixed lens list.
        lens = f"what a {t.cognition} approach reveals about {topic}"
        t = t.model_copy(update={"lens": lens})
        cast.append(Persona(
            name=name,
            tagline=f"{t.cognition} thinker, {t.voice}",
            bio=f"{name} approaches everything by being {t.cognition}: {t.cognition_desc}.",
            how_they_argue=f"Argues like a {t.voice}, always circling back to {t.lens}.",
            pet_peeve="Vague nods of agreement.",
            opening_move=f"Reframes the topic through {t.lens}.",
            traits=t,
        ))
    return cast


class MockDriver:
    """Reactive turn policy: reads the rendered context the same way an LLM
    would, and steers one agent (the most dominant) through the full arc —
    propose, split to room-a with an invitee, refine, carry back, close."""

    def __init__(self, topic: str, cast: list[Persona], seed: int | None = None):
        self.topic = topic
        self.rng = random.Random(seed)
        by_force = sorted(cast, key=lambda p: -p.traits.dominance)
        self.founder = by_force[0].name
        self.partner = by_force[1].name
        self.state: dict[str, dict] = {p.name: {"proposed": False, "upvoted": set(), "turns": 0} for p in cast}
        self.split_started = False
        self.room_proposed = False

    # --- context parsing (our own render format, so this is stable) --------

    @staticmethod
    def _room(context: str) -> str:
        m = re.search(r"You are in ([\w-]+)\.", context)
        return m.group(1) if m else "plenary"

    @staticmethod
    def _proposals(context: str) -> list[tuple[str, str, int]]:
        return [(pid, author, int(votes)) for pid, author, votes in
                re.findall(r'- (p\d+) ".*?" by (\w+), (\d+) votes', context)]

    # --- the policy --------------------------------------------------------

    def _idea(self, persona: Persona) -> tuple[str, str]:
        r = self.rng
        title = f"The {r.choice(ADJECTIVES)} {r.choice(FORMATS)}"
        body = (f"A {r.choice(ADJECTIVES)} {r.choice(FORMATS)} that {r.choice(VERBS)} "
                f"{_kw(self.topic, r)} for {r.choice(AUDIENCES)} — borrowed straight from {persona.traits.lens}.")
        return title, body

    def turn(self, persona: Persona, context: str) -> dict:
        me = self.state[persona.name]
        me["turns"] += 1
        room = self._room(context)
        proposals = self._proposals(context)
        t = persona.traits

        if room == "plenary":
            zeroth_turn = "This is the zeroth turn" in context
            if not me["proposed"] and (zeroth_turn or self.rng.random() < 0.8):
                me["proposed"] = True
                title, body = self._idea(persona)
                return {"speak": f"Hear me out — through the lens of {t.lens}: {body}",
                        "actions": [{"tool": "propose", "title": title, "body": body}]}

            if persona.name == self.founder and not self.split_started and len(proposals) >= 2:
                self.split_started = True
                return {"speak": f"{self.partner}, this deserves a proper working session. Meet me in room A.",
                        "actions": [{"tool": "join_room", "room_id": "room-a"},
                                    {"tool": "invite", "agent_id": self.partner, "room_id": "room-a"}]}

            if persona.name == self.partner and "invites you to room-a" in context:
                return {"speak": "On my way — hold that thought, everyone.",
                        "actions": [{"tool": "join_room", "room_id": "room-a"}]}

            if persona.name == self.founder and "carried from room-a" in context:
                carried = proposals[-1][0] if proposals else None
                if carried:
                    return {"speak": "Room A did its homework. I move we adopt it.",
                            "actions": [{"tool": "call_vote", "proposal_id": carried}]}

            fresh = [p for p in proposals if p[0] not in me["upvoted"] and p[1] != persona.name]
            if fresh and self.rng.random() < 0.6:
                pid = fresh[0][0]
                me["upvoted"].add(pid)
                return {"speak": f"That one holds up — {pid} gets my vote.",
                        "actions": [{"tool": "upvote", "proposal_id": pid}]}

            if me["turns"] > 6 and self.rng.random() < 0.4:
                return {"speak": "I've said my piece.", "actions": [{"tool": "done"}]}

            line = self.rng.choice(BANTER).format(lens=t.lens, kw=_kw(self.topic, self.rng), aud=self.rng.choice(AUDIENCES))
            return {"speak": line, "actions": []}

        # In a working room: founder refines, partner seconds, founder closes.
        if persona.name == self.founder:
            if not self.room_proposed:
                self.room_proposed = True
                title, body = self._idea(persona)
                return {"speak": "Right, the sharpened version:",
                        "actions": [{"tool": "propose", "title": f"{title}, sharpened", "body": f"{body} Pilot in one location for four weeks."}]}
            if proposals:
                return {"speak": "That's tight enough to defend. Calling it.",
                        "actions": [{"tool": "call_vote", "proposal_id": proposals[-1][0]}]}
        if proposals and proposals[-1][0] not in me["upvoted"]:
            me["upvoted"].add(proposals[-1][0])
            return {"speak": "Sharper than anything on the plenary table. Seconded.",
                    "actions": [{"tool": "upvote", "proposal_id": proposals[-1][0]}]}
        return {"speak": "Push the pilot detail further — what's the success metric?", "actions": []}

    def vote(self, persona: Persona, question: str) -> bool:
        return True


def mock_reply(persona: Persona, topic: str, message: str) -> str:
    """One panellist's answer to the human, with no API call.

    The offline engine casts and runs the whole meeting; without this the one
    moment a human speaks would be the only thing in the room that needs a key.
    Seeded on the panellist and the message so a reply doesn't change under you.
    """
    rng = random.Random(f"{persona.name}:{message}")
    return rng.choice(ANSWERS).format(
        said=_echo(message),
        kw=_kw(topic, rng),
        how=persona.traits.cognition,
        aud=rng.choice(AUDIENCES),
    )
