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

from .llm import complete_json

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
]

# The domain they drag every conversation back to. Dealt without replacement.
LENS = [
    "marine biology", "freight logistics", "tabletop game design",
    "emergency medicine", "street food carts", "cathedral architecture",
    "competitive speedrunning", "actuarial insurance", "beekeeping",
    "air traffic control", "second-hand bookshops", "municipal plumbing",
]

# Delivery style only — orthogonal to cognition on purpose. Dealt without replacement.
VOICE = [
    "deadpan stand-up comic", "over-caffeinated hype man", "weary night-shift sysadmin",
    "hushed nature documentarian", "conspiracy-corkboard obsessive", "noir detective",
    "kindergarten teacher", "sports commentator", "disappointed Victorian naturalist",
]


class Traits(BaseModel):
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


def sample_traits(n: int, rng: random.Random) -> list[Traits]:
    """Deal n orthogonal trait sets.

    Dominance is the one axis we don't leave to chance: exactly one agent gets
    to be forceful. Otherwise the serious high-dominance archetype turns every
    meeting into a monologue.
    """
    if n > min(len(COGNITION), len(LENS), len(VOICE)):
        raise ValueError(f"can't deal {n} distinct agents from the trait pools")

    cognitions = rng.sample(COGNITION, n)
    lenses = rng.sample(LENS, n)
    voices = rng.sample(VOICE, n)

    dominance = [rng.randint(1, 3) for _ in range(n)]
    dominance[rng.randrange(n)] = rng.choice([4, 5])

    return [
        Traits(
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
- Do not name them after their trait. No "Riley Risk", no "Dr. Contrarian".
- Give them a specific past, not a vague one. "Ran logistics for a touring \
circus" beats "has experience in operations".

Return JSON with exactly these keys: name, tagline, bio, how_they_argue, \
pet_peeve, opening_move. All values are strings. tagline is under 10 words, \
bio is 2-3 sentences, the rest are one sentence each."""


def _prompt(t: Traits, topic: str, existing: list[Persona]) -> str:
    lines = [
        f"The panel is brainstorming: {topic}",
        "",
        "Build a panellist with these traits:",
        f"- Thinks by being {t.cognition}: {t.cognition_desc}",
        f"- Drags every problem back to {t.lens}",
        f"- Talks like a {t.voice}",
        f"- Risk appetite {t.risk}/5, abstraction {t.abstraction}/5, forcefulness {t.dominance}/5",
    ]
    if existing:
        lines += ["", "Already on the panel — be unmistakably different from all of them:"]
        lines += [f"- {p.name}: {p.tagline}" for p in existing]
    return "\n".join(lines)


def generate_cast(topic: str, n: int = 5, seed: int | None = None) -> list[Persona]:
    """Generate n personalities, sequentially so each can differentiate itself."""
    rng = random.Random(seed)
    cast: list[Persona] = []
    for traits in sample_traits(n, rng):
        data = complete_json(SYSTEM, _prompt(traits, topic, cast), seed=seed)
        cast.append(Persona(**data, traits=traits))
    return cast


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a brainstorming panel.")
    ap.add_argument("topic", help="what the panel will brainstorm about")
    ap.add_argument("-n", type=int, default=5, help="number of panellists (default 5)")
    ap.add_argument("--seed", type=int, help="reproducible cast")
    ap.add_argument("--json", action="store_true", help="dump raw JSON")
    ap.add_argument("--traits-only", action="store_true", help="show the sampled traits, no API calls")
    args = ap.parse_args()

    if args.traits_only:
        for t in sample_traits(args.n, random.Random(args.seed)):
            print(t.model_dump_json())
        return

    cast = generate_cast(args.topic, args.n, args.seed)
    if args.json:
        print(json.dumps([p.model_dump() for p in cast], indent=2))
        return
    for p in cast:
        t = p.traits
        print(f"\n\033[1m{p.name}\033[0m — {p.tagline}")
        print(f"  {t.cognition} · {t.lens} · {t.voice} · "
              f"risk {t.risk} abstraction {t.abstraction} force {t.dominance}")
        print(f"  {p.bio}")
        print(f"  Argues: {p.how_they_argue}")
        print(f"  Hates:  {p.pet_peeve}")
        print(f"  Opens:  {p.opening_move}")


if __name__ == "__main__":
    main()
