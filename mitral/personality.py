"""Generate a cast of brainstorming personalities.

The hard part is not writing personalities, it's writing personalities that
don't collapse into the same three ideas. Two things make that work:

1.  Traits are sampled on *orthogonal axes* and the discrete ones are dealt
    without replacement, so no two agents can share a way of thinking or a
    domain to think about it with.
2.  `voice` is deliberately independent of `cognition`. The funny one is funny
    in delivery while still reasoning rigorously — humour is a costume, not a
    brain. That's what stops the comic relief from being useless.
"""

import argparse
import json
import random

from pydantic import BaseModel, Field

from .llm import FAST_MODEL, complete_json

# How the agent actually generates ideas. Dealt without replacement.
COGNITION = [
    ("first-principles", "strips the problem to physics and money and rebuilds from there"),
    ("analogical", "solves it by finding a solved problem in a distant field"),
    ("contrarian", "assumes the obvious answer is wrong and looks for why"),
    ("combinatorial", "mashes unrelated existing things together and sees what survives"),
    ("empirical", "wants the cheapest experiment that would kill the idea today"),
    ("constraint-driven", "invents a brutal limitation and designs inside it"),
    ("narrative", "imagines one specific user's day and works backwards"),
    ("adversarial", "designs the thing by first designing how to break it"),
    ("historical", "digs up what was already tried here and why it died"),
    ("systemic", "hunts the feedback loop that keeps regenerating the problem"),
    ("extrapolative", "asks what this looks like at 100x and designs for that"),
    ("probabilistic", "thinks in odds and expected value, not in outcomes"),
    ("subtractive", "improves it by deleting parts until something finally breaks"),
    ("inversion", "states the goal backwards and asks how you'd guarantee failure"),
    ("economic", "follows the incentives and asks who profits from each version"),
    ("ethnographic", "watches what people actually do instead of what they say"),
    ("taxonomic", "sorts the space into categories until the empty box is obvious"),
    ("temporal", "asks what changes if this happens in a week versus in a year"),
    ("resource-swap", "asks what becomes possible if one scarce input became free"),
    ("simulation", "plays the idea forward three moves and reports the board"),
]

# The domain they drag every conversation back to. Dealt without replacement.
LENS = [
    "marine biology", "freight logistics", "tabletop game design",
    "emergency medicine", "street food carts", "cathedral architecture",
    "competitive speedrunning", "actuarial insurance", "beekeeping",
    "air traffic control", "second-hand bookshops", "municipal plumbing",
    "wildfire fighting", "orchestral conducting", "professional wrestling booking",
    "antarctic research stations", "theme park queue design", "forensic accounting",
    "stage magic", "field archaeology",
]

# Delivery style only — orthogonal to cognition on purpose. Dealt without replacement.
VOICE = [
    "deadpan stand-up comic", "over-caffeinated hype man", "weary night-shift sysadmin",
    "hushed nature documentarian", "conspiracy-corkboard obsessive", "noir detective",
    "kindergarten teacher", "sports commentator", "disappointed Victorian naturalist",
    "true-crime podcast host", "airline pilot on the intercom", "medieval town crier",
    "livestock auctioneer", "late-night infomercial host", "shipping forecast announcer",
    "grumpy taxi driver", "wine sommelier", "military drill instructor",
    "1950s newsreel announcer", "gossip columnist",
]

# The grounded equivalents. Same axes, no costume: these are colleagues in a
# meeting, not characters at a fancy-dress party. Use these when the topic is
# real work ("how should we architect this service") and a beekeeper would just
# be noise.

# Grounded stand-in for LENS: what they're personally on the hook for. Applies
# to any professional problem, unlike a domain.
STAKE = [
    "whoever has to maintain this in two years",
    "whoever has to pay for it",
    "whoever has to sell or explain it to outsiders",
    "the newest person on the team, who has to understand it",
    "someone who got badly burned doing this before",
    "the end user, who never reads the docs",
    "security and everything that can be abused",
    "the deadline, and what actually ships this month",
    "whoever is on call when it breaks at 3am",
    "the competitor who would love this to fail",
    "the people whose day-to-day work this changes",
    "legal, compliance, and whatever the regulator makes of it",
    "the customer who churns quietly instead of complaining",
    "whoever has to migrate off this thing later",
    "the support team who gets the tickets about it",
    "the people who will never be in a room like this one",
    "the data, and what happens to it the day this is switched off",
    "whoever has to test it and prove it works",
    "the smallest customer, who can't afford the expensive tier",
    "reputation, and what this looks like on the front page",
]

# Grounded stand-in for VOICE: temperament, still orthogonal to cognition.
TEMPERAMENT = [
    "upbeat and encouraging, builds on other people's ideas out loud",
    "dry and funny, undercuts tension with a one-liner then makes the point",
    "serious and analytical, speaks in numbers and tradeoffs",
    "cautious, always names the failure mode first",
    "blunt and skeptical, says the unpopular thing without softening it",
    "warm facilitator, keeps pulling the quiet people back in",
    "impatient, wants a decision and visibly hates circling",
    "curious, answers with a question that reframes the problem",
    "quiet and sparing, but what they say lands hard",
    "diplomatic, restates each disagreement until both sides recognise it",
    "stubbornly literal, won't move on until the terms are actually defined",
    "playful, tests an idea by exaggerating it until it breaks",
    "a magpie, keeps dragging in something they read this week",
    "earnest and sincere, with no irony whatsoever",
    "self-deprecating, floats ideas as if they're probably stupid",
    "competitive, treats the whiteboard like a scoreboard",
    "a long-winded storyteller who does eventually land somewhere useful",
    "anxious, wants everything written down before agreeing to it",
    "unflappable, same tone in a crisis as over coffee",
    "a wry veteran who has sat through this exact meeting before",
]

MODES = {"wild": (LENS, VOICE), "grounded": (STAKE, TEMPERAMENT)}


class Traits(BaseModel):
    mode: str
    cognition: str
    cognition_desc: str
    lens: str
    voice: str
    risk: int = Field(ge=1, le=5)        # 1 = safe and shippable, 5 = moonshot
    abstraction: int = Field(ge=1, le=5)  # 1 = tactical detail, 5 = systemic
    dominance: int = Field(ge=1, le=5)    # how hard they push their own idea


class Persona(BaseModel):
    name: str
    tagline: str
    bio: str
    how_they_argue: str
    pet_peeve: str
    opening_move: str
    traits: Traits


def sample_traits(
    n: int, rng: random.Random, mode: str = "grounded", used: list[Traits] | None = None
) -> list[Traits]:
    """Deal n orthogonal trait sets.

    Dominance is the one axis we don't leave to chance: exactly one agent gets
    to be forceful. Otherwise the serious high-dominance archetype turns every
    meeting into a monologue.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}, expected one of {sorted(MODES)}")
    lens_pool, voice_pool = MODES[mode]
    if used:
        # Adding to a live panel: the traits already in the room are spent, so
        # the newcomer stays orthogonal to everyone rather than to nobody.
        spent_cog = {t.cognition for t in used}
        cognition_pool = [c for c in COGNITION if c[0] not in spent_cog]
        lens_pool = [l for l in lens_pool if l not in {t.lens for t in used}]
        voice_pool = [v for v in voice_pool if v not in {t.voice for t in used}]
    else:
        cognition_pool = COGNITION
    if n > min(len(cognition_pool), len(lens_pool), len(voice_pool)):
        raise ValueError("the trait pools are exhausted — that's as big as a panel gets")

    cognitions = rng.sample(cognition_pool, n)
    lenses = rng.sample(lens_pool, n)
    voices = rng.sample(voice_pool, n)

    dominance = [rng.randint(1, 3) for _ in range(n)]
    dominance[rng.randrange(n)] = rng.choice([4, 5])

    return [
        Traits(
            mode=mode,
            cognition=cog,
            cognition_desc=desc,
            lens=lens,
            voice=voice,
            risk=rng.randint(1, 5),
            abstraction=rng.randint(1, 5),
            dominance=dom,
        )
        for (cog, desc), lens, voice, dom in zip(cognitions, lenses, voices, dominance)
    ]


SYSTEM = """You invent members of a brainstorming panel. Each one is a real \
character with a real way of thinking, not a job title with an adjective.

Hard rules:
- The voice is a delivery style, NOT their intelligence. A character with a \
comic voice must still produce genuinely sharp, useful ideas — they just phrase \
them funny. Never write a character whose contribution is only jokes.
- Do NOT give them a human name. Never "Marcus Chen", never "Sarah Patel". \
Each panellist is known by a title: "The" plus one evocative noun — The Dreamer, \
The Whisperer, The Undertaker, The Cartographer, The Magpie, The Lighthouse \
Keeper. Two or three words at most.
- The noun should hint at how they think or what they care about without \
naming the trait outright. "The Locksmith" for someone adversarial, yes; \
"The Adversarial One", no.
- Every title on one panel must be a different noun, and none may repeat a \
title already used above.
- Give them a specific past, not a vague one. "Ran logistics for a touring \
circus" beats "has experience in operations".

Return JSON with exactly these keys: name, tagline, bio, how_they_argue, \
pet_peeve, opening_move. All values are strings. tagline is under 10 words, \
bio is 2-3 sentences, the rest are one sentence each."""

GROUNDED_SYSTEM = """You invent members of a brainstorming panel. These are \
ordinary competent colleagues in a real meeting — no costumes, no gimmicks, no \
quirky hobbies standing in for a personality.

Hard rules:
- Their temperament is how they behave in the room, NOT their intelligence. The \
funny one is still sharp; the cautious one still ships things.
- They are credible on the topic at hand. Give them plausible relevant \
experience, not an exotic backstory.
- Do NOT give them a human name. Never "Marcus Chen", never "Sarah Patel". \
Each panellist is known by a title: "The" plus one evocative noun — The Dreamer, \
The Whisperer, The Undertaker, The Cartographer, The Magpie, The Lighthouse \
Keeper. Two or three words at most.
- The noun should hint at how they think or what they care about without \
naming the trait outright. "The Locksmith" for someone adversarial, yes; \
"The Adversarial One", no.
- Every title on one panel must be a different noun, and none may repeat a \
title already used above.
- What makes them distinct is what they push for and what they refuse to let \
slide, not an accent or a catchphrase.

Return JSON with exactly these keys: name, tagline, bio, how_they_argue, \
pet_peeve, opening_move. All values are strings. tagline is under 10 words, \
bio is 2-3 sentences, the rest are one sentence each."""


def _system(mode: str) -> str:
    return SYSTEM if mode == "wild" else GROUNDED_SYSTEM


def _prompt(t: Traits, topic: str, existing: list[Persona]) -> str:
    lines = [
        f"The panel is brainstorming: {topic}",
        "",
        "Build a panellist with these traits:",
        f"- Thinks by being {t.cognition}: {t.cognition_desc}",
    ]
    if t.mode == "wild":
        lines += [
            f"- Drags every problem back to {t.lens}",
            f"- Talks like a {t.voice}",
        ]
    else:
        lines += [
            f"- Argues on behalf of {t.lens}",
            f"- In the room they are {t.voice}",
        ]
    lines += [
        f"- Risk appetite {t.risk}/5, abstraction {t.abstraction}/5, forcefulness {t.dominance}/5",
    ]
    if existing:
        lines += [
            "",
            "Already on the panel. Read these properly — the new panellist must not "
            "share a career, an industry, a former employer type, or a seniority "
            "story with any of them:",
        ]
        for p in existing:
            lines.append(f"- {p.name} ({p.tagline}): {p.bio}")
        lines += [
            "",
            "If the people above are all ex-startup operators, this one is not. Draw "
            "their background from somewhere else entirely: public sector, trades, "
            "academia, the military, a family business, a regulated industry, a job "
            "they left. Range across ages and career stages too.",
        ]
    return "\n".join(lines)


def _normalise(text: str) -> str:
    return " ".join("".join(c for c in text.lower() if c.isalnum() or c.isspace()).split())


def _collides(p: Persona, cast: list[Persona]) -> str | None:
    """Whether this persona is a copy of one we already have.

    Showing the model previous bios stops backgrounds converging, but it also
    hands it something to plagiarise — it will occasionally return an earlier
    bio verbatim. Catch that here rather than shipping twins.
    """
    for other in cast:
        if _normalise(p.name) == _normalise(other.name):
            return f"the name {other.name!r}"
        if _normalise(p.bio) == _normalise(other.bio):
            return f"{other.name}'s bio, word for word"
    return None


def _write_persona(
    traits: Traits, topic: str, cast: list[Persona], seed: int | None, mode: str
) -> Persona:
    """One panellist who isn't a copy of anyone already in the room."""
    prompt = _prompt(traits, topic, cast)
    for _ in range(3):
        data = complete_json(_system(mode), prompt, seed=seed, model=FAST_MODEL)
        person = Persona(**data, traits=traits)
        clash = _collides(person, cast)
        if clash is None:
            return person
        # Nudge off the collision and re-roll the sampler by dropping the seed.
        prompt += (
            f"\n\nYour last attempt reused {clash}. Write a completely "
            "different person: different name, different career, different city, "
            "different decade of experience."
        )
        seed = None
    return person


def generate_cast(
    topic: str, n: int = 5, seed: int | None = None, mode: str = "grounded"
) -> list[Persona]:
    """Generate n personalities, sequentially so each can differentiate itself."""
    return list(generate_cast_iter(topic, n, seed, mode))


def generate_cast_iter(
    topic: str, n: int = 5, seed: int | None = None, mode: str = "grounded"
):
    """Yield personalities as soon as each sequential model call finishes."""
    rng = random.Random(seed)
    cast: list[Persona] = []
    for traits in sample_traits(n, rng, mode):
        person = _write_persona(traits, topic, cast, seed, mode)
        cast.append(person)
        yield person


def add_panellist(
    topic: str, cast: list[Persona], seed: int | None = None, mode: str = "grounded"
) -> Persona:
    """One more panellist for a panel that's already running."""
    rng = random.Random(seed)
    traits = sample_traits(1, rng, mode, used=[p.traits for p in cast])[0]
    return _write_persona(traits, topic, cast, seed, mode)


class Pitch(BaseModel):
    """One panellist's opening idea."""

    idea: str = Field(description="the idea in under 8 words")
    mechanism: str = Field(description="the underlying lever, under 10 words — used to de-duplicate")
    pitch: str = Field(description="how they'd say it out loud, in their voice")
    sharp_edge: str = Field(description="the concrete detail that makes it more than a vibe")


PITCH_SYSTEM = """You are speaking as one member of a brainstorming panel. \
Give your first idea on the topic.

Hard rules:
- The idea must be genuinely usable, not a joke. Your voice is how you say it, \
not how well you think.
- The IDEA ITSELF must be the product of your thinking style, not just the way \
you introduce it. Someone shown only the idea, with your name removed, should be \
able to guess which thinking style produced it. If your style is adversarial, the \
idea is built around a break; if it is subtractive, the idea is something removed; \
if it is historical, the idea rests on a specific thing that already happened. An \
ordinary idea with your style bolted onto the first sentence is a failure.
- Be specific. Name a thing, a place, a number, a mechanism. No "leverage synergies".
- Do not repeat anyone else's MECHANISM. Two ideas that move the same lever are the \
same idea, however differently they are named — "refrigerated pods in car parks" and \
"shipping-container kitchens in bus depots" are one idea, not two. Read the pitches \
below in full and pick a different lever, not a different wrapper.

Return JSON with exactly these keys: idea, mechanism, pitch, sharp_edge. All \
strings. idea is under 8 words, mechanism names the underlying lever in under 10 \
words, pitch is 2-3 sentences in your voice, sharp_edge is one sentence."""


def _pitch_prompt(p: Persona, topic: str, said: list[tuple[Persona, Pitch]]) -> str:
    t = p.traits
    lines = [
        f"Topic: {topic}",
        "",
        f"You are {p.name} — {p.tagline}.",
        f"{p.bio}",
        f"You think by being {t.cognition}: {t.cognition_desc}",
        f"You drag every problem back to {t.lens}." if t.mode == "wild"
        else f"You argue on behalf of {t.lens}.",
        f"You talk like a {t.voice}." if t.mode == "wild"
        else f"In the room you are {t.voice}.",
        f"Risk appetite {t.risk}/5, abstraction {t.abstraction}/5.",
        f"You argue like this: {p.how_they_argue}",
    ]
    lines += [
        "",
        f"Your idea must visibly be the work of someone {t.cognition_desc}.",
    ]
    if said:
        lines += [
            "",
            "Already on the table. Your mechanism must differ from every mechanism "
            "listed here — not just the wording:",
        ]
        for sp, sq in said:
            lines += [
                f"- {sp.name} — {sq.idea}",
                f"  mechanism: {sq.mechanism}",
                f"  {sq.pitch}",
            ]
    return "\n".join(lines)


def one_take(
    p: Persona, topic: str, said: list[tuple[Persona, Pitch]], seed: int | None = None
) -> Pitch:
    """A single opening idea, told what's already been said so it doesn't repeat it."""
    return Pitch(**complete_json(PITCH_SYSTEM, _pitch_prompt(p, topic, said), seed=seed))


def first_takes(cast: list[Persona], topic: str, seed: int | None = None) -> list[Pitch]:
    """Each panellist's opening idea, in order, each aware of what came before."""
    said: list[tuple[Persona, Pitch]] = []
    for p in cast:
        said.append((p, one_take(p, topic, said, seed)))
    return [q for _, q in said]


class Deliberation(BaseModel):
    """What the panel does with the ideas once they're all on the table."""

    plan_speaker: str = Field(description="name of the panellist who makes it testable")
    plan_text: str = Field(description="how they'd make the leading idea testable, in their voice")
    test_speaker: str = Field(description="name of the panellist who stress-tests it")
    test_text: str = Field(description="the failure mode they push on, in their voice")
    winner_speaker: str = Field(description="name of the panellist whose idea the panel backs")
    why: str = Field(description="one sentence on why that idea won")


DELIBERATE_SYSTEM = """You are running a brainstorming panel that has just \
heard everyone's opening idea. Now the panel does three things: makes the \
strongest idea testable, stress-tests it, and picks a winner.

Hard rules:
- Pick the two speakers from the panel below by how they think. The one who \
makes it testable should be someone empirical, pragmatic or constraint-driven; \
the one who stress-tests should be someone adversarial, contrarian or cautious. \
Do not use the same person twice.
- Write each line in that person's actual voice, the way they'd say it out loud.
- Be concrete. Name the pilot, the number, the week, the thing that breaks. \
"We should validate our assumptions" is a failure.
- The winner is the idea with the sharpest mechanism, not the loudest pitch. It \
does not have to be the first one.

Return JSON with exactly these keys: plan_speaker, plan_text, test_speaker, \
test_text, winner_speaker, why. All strings. plan_text and test_text are 1-2 \
sentences each, why is one sentence."""


def _panel_brief(cast: list[Persona], topic: str, pitches: list[Pitch]) -> str:
    lines = [f"Topic: {topic}", "", "The panel and what each of them just pitched:"]
    for p, q in zip(cast, pitches):
        t = p.traits
        lines += [
            f"- {p.name} — {p.tagline}",
            f"  thinks by being {t.cognition}: {t.cognition_desc}",
            f"  in the room they are {t.voice}",
            f"  pitched: {q.idea} (mechanism: {q.mechanism})",
            f"  {q.pitch}",
        ]
    return "\n".join(lines)


def deliberate(
    cast: list[Persona], topic: str, pitches: list[Pitch], seed: int | None = None
) -> Deliberation:
    """The plan beat, the stress-test beat, and the panel's verdict."""
    data = complete_json(DELIBERATE_SYSTEM, _panel_brief(cast, topic, pitches), seed=seed)
    return Deliberation(**data)


REPLY_SYSTEM = """You are one member of a brainstorming panel. Someone in the \
room has just said something to you. Answer them in one or two sentences, in \
your own voice.

Hard rules:
- Actually engage with what they said. Take it somewhere, push back on it, or \
build on it — do not just acknowledge it and promise to consider it later.
- Stay in character and keep thinking the way you think.
- No preamble, no "great question". Just the reply.

Return JSON with exactly one key: text."""


def reply(p: Persona, topic: str, message: str, seed: int | None = None) -> str:
    """One panellist's answer to something a human said in the room."""
    t = p.traits
    prompt = "\n".join([
        f"Topic: {topic}",
        "",
        f"You are {p.name} — {p.tagline}.",
        p.bio,
        f"You think by being {t.cognition}: {t.cognition_desc}",
        f"You drag every problem back to {t.lens}." if t.mode == "wild"
        else f"You argue on behalf of {t.lens}.",
        f"You talk like a {t.voice}." if t.mode == "wild"
        else f"In the room you are {t.voice}.",
        f"You argue like this: {p.how_they_argue}",
        f"It bugs you when: {p.pet_peeve}",
        "",
        f"They said: {message}",
    ])
    data = complete_json(REPLY_SYSTEM, prompt, seed=seed)
    return str(data["text"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a brainstorming panel.")
    ap.add_argument("topic", help="what the panel will brainstorm about")
    ap.add_argument("-n", type=int, default=6, help="number of panellists (default 6, max 20)")
    ap.add_argument("--seed", type=int, help="reproducible cast")
    ap.add_argument("--mode", choices=sorted(MODES), default="grounded",
                    help="grounded = normal colleagues, wild = eccentric outsiders")
    ap.add_argument("--json", action="store_true", help="dump raw JSON")
    ap.add_argument("--pitch", action="store_true", help="also generate each panellist's first idea")
    ap.add_argument("--traits-only", action="store_true", help="show the sampled traits, no API calls")
    args = ap.parse_args()

    if args.traits_only:
        for t in sample_traits(args.n, random.Random(args.seed), args.mode):
            print(t.model_dump_json())
        return

    cast = generate_cast(args.topic, args.n, args.seed, args.mode)
    takes = first_takes(cast, args.topic, args.seed) if args.pitch else [None] * len(cast)
    if args.json:
        print(json.dumps([
            {**p.model_dump(), "first_take": q.model_dump() if q else None}
            for p, q in zip(cast, takes)
        ], indent=2))
        return
    for p, q in zip(cast, takes):
        t = p.traits
        print(f"\n\033[1m{p.name}\033[0m — {p.tagline}")
        print(f"  {t.cognition} · {t.lens} · {t.voice} · "
              f"risk {t.risk} abstraction {t.abstraction} force {t.dominance}")
        print(f"  {p.bio}")
        print(f"  Argues: {p.how_they_argue}")
        print(f"  Hates:  {p.pet_peeve}")
        print(f"  Opens:  {p.opening_move}")
        if q:
            print(f"\n  \033[1m>> {q.idea}\033[0m  ({q.mechanism})")
            print(f"  {q.pitch}")
            print(f"  Edge:   {q.sharp_edge}")


if __name__ == "__main__":
    main()
