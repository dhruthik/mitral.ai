from enum import Enum

from pydantic import BaseModel


class Stance(str, Enum):
    DREAMER = "dreamer"
    SKEPTIC = "skeptic"
    PRAGMATIST = "pragmatist"
    ADVOCATE = "advocate"
    WILDCARD = "wildcard"


STANCE_LABELS: dict[Stance, str] = {
    Stance.DREAMER: "the dreamer",
    Stance.SKEPTIC: "the skeptic",
    Stance.PRAGMATIST: "the pragmatist",
    Stance.ADVOCATE: "the advocate",
    Stance.WILDCARD: "the wildcard",
}


class Personality(BaseModel):
    id: str
    name: str
    stance: Stance
    label: str
    color: str | None = None
