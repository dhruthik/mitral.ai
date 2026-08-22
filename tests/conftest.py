import random

import pytest

from mitral.engine.factory import new_session
from mitral.models.personality import Personality, STANCE_LABELS, Stance


@pytest.fixture
def rng() -> random.Random:
    return random.Random(42)


def make_cast() -> list[Personality]:
    """Fixed 5-agent roster: one of each stance, deterministic ids/names."""
    return [
        Personality(id="d", name="D", stance=Stance.DREAMER, label=STANCE_LABELS[Stance.DREAMER], color="#111"),
        Personality(id="s", name="S", stance=Stance.SKEPTIC, label=STANCE_LABELS[Stance.SKEPTIC], color="#222"),
        Personality(id="p", name="P", stance=Stance.PRAGMATIST, label=STANCE_LABELS[Stance.PRAGMATIST], color="#333"),
        Personality(id="a", name="A", stance=Stance.ADVOCATE, label=STANCE_LABELS[Stance.ADVOCATE], color="#444"),
        Personality(id="w", name="W", stance=Stance.WILDCARD, label=STANCE_LABELS[Stance.WILDCARD], color="#555"),
    ]


@pytest.fixture
def cast() -> list[Personality]:
    return make_cast()


@pytest.fixture
def session(cast, rng):
    # room0 = d, a, w (wildcard alternation puts the lone wildcard in room0)
    # room1 = s, p
    return new_session("a coffee shop that's only open at night", cast=cast, rng=rng, session_id="sess-1")
