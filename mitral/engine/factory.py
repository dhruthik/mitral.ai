import random
import uuid

from mitral.models.agent import AgentRuntime
from mitral.models.personality import Personality
from mitral.models.session import Room, Session
from mitral.personalities.builtin import ROOM_NAME_POOLS, assign_rooms, spawn_cast


def new_session(
    idea: str,
    cast: list[Personality] | None = None,
    rng: random.Random | None = None,
    session_id: str | None = None,
) -> Session:
    rng = rng or random.Random()
    cast = cast or spawn_cast(rng)
    assignment = assign_rooms(cast, rng)

    agents = {
        p.id: AgentRuntime(
            agent_id=p.id,
            personality=p,
            room_id="room0" if p.id in assignment["room0"] else "room1",
        )
        for p in cast
    }

    rooms = {
        "room0": Room(
            id="room0",
            title=rng.choice(ROOM_NAME_POOLS["room0"]),
            tag="1",
            color="#7C5CE8",
            member_ids=assignment["room0"],
        ),
        "room1": Room(
            id="room1",
            title=rng.choice(ROOM_NAME_POOLS["room1"]),
            tag="2",
            color="#2FB8A6",
            member_ids=assignment["room1"],
        ),
        "q": Room(
            id="q",
            title="The Quorum",
            tag="Q",
            color="#E0B93D",
            member_ids=list(agents.keys()),
        ),
    }

    return Session(id=session_id or uuid.uuid4().hex, idea=idea, agents=agents, rooms=rooms)
