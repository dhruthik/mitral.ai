"""Default cast spawning + room-split, ported from the UI team's mocked
prototype (genCast/room-assignment in prototype/brainstorm-stage.html) so the
orchestrator is demoable standalone before real personality-creation work
lands, and produces the same room split the frontend already expects."""

import random

from mitral.models.personality import STANCE_LABELS, Personality, Stance

NAME_POOLS: dict[Stance, list[str]] = {
    Stance.DREAMER: ["Nova", "Lumi", "Sol", "Aria", "Fizz"],
    Stance.SKEPTIC: ["Rex", "Vera", "Grim", "Nyx", "Sten"],
    Stance.PRAGMATIST: ["June", "Otto", "Meg", "Bo", "Wren"],
    Stance.ADVOCATE: ["Priya", "Sam", "Ida", "Kae", "Rosa"],
    Stance.WILDCARD: ["Zed", "Pip", "Moxo", "Blip", "Q"],
}

UI_COLORS = [
    "#7C5CE8", "#E09A2F", "#E86A8A", "#2FB8A6",
    "#4C9BE0", "#C05CE8", "#64748B", "#D96A4A",
]

ROOM_NAME_POOLS = {
    "room0": ["The Dream Lab", "Blue Sky Room", "The Launchpad", "The Moonshot Suite"],
    "room1": ["The Reality Check", "The Workbench", "The Proving Ground", "The Fine Print"],
}


def spawn_cast(rng: random.Random | None = None) -> list[Personality]:
    rng = rng or random.Random()
    stances = [Stance.DREAMER, Stance.SKEPTIC, Stance.PRAGMATIST, Stance.ADVOCATE, Stance.WILDCARD]
    if rng.random() < 0.5:
        stances.append(rng.choice(stances))

    used_names: set[str] = set()
    colors = UI_COLORS[:]
    rng.shuffle(colors)

    cast = []
    for i, stance in enumerate(stances):
        options = [n for n in NAME_POOLS[stance] if n not in used_names]
        name = rng.choice(options) if options else f"{stance.value.title()}{i}"
        used_names.add(name)
        cast.append(
            Personality(
                id=name.lower(),
                name=name,
                stance=stance,
                label=STANCE_LABELS[stance],
                color=colors[i % len(colors)],
            )
        )
    return cast


def assign_rooms(cast: list[Personality], rng: random.Random | None = None) -> dict[str, list[str]]:
    """Mirrors the prototype's divergers/convergers split: dreamers+advocates
    go to room0, skeptics+pragmatists to room1, wildcards alternate between."""
    rng = rng or random.Random()
    divergers = [p.id for p in cast if p.stance in (Stance.DREAMER, Stance.ADVOCATE)]
    convergers = [p.id for p in cast if p.stance in (Stance.SKEPTIC, Stance.PRAGMATIST)]
    wildcards = [p.id for p in cast if p.stance == Stance.WILDCARD]

    for i, agent_id in enumerate(wildcards):
        (divergers if i % 2 == 0 else convergers).append(agent_id)

    if not divergers and convergers:
        divergers.append(convergers.pop())
    if not convergers and divergers:
        convergers.append(divergers.pop())

    return {"room0": divergers, "room1": convergers}
