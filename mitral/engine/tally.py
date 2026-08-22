from mitral.models.session import Room, Session


def wrap_ready(room: Room, session: Session) -> bool:
    members = room.member_ids
    if not members:
        return False
    votes = sum(
        1
        for aid in members
        if (last := session.agents[aid].last_action) and last.tool == "propose_wrap"
    )
    return votes / len(members) >= session.wrap_quorum


def quorum_tally(session: Session) -> dict[str, int]:
    tally = {"room0": 0, "room1": 0}
    for agent in session.agents.values():
        last = agent.last_action
        if last and last.tool == "cast_vote":
            choice = last.payload.get("room_choice")
            if choice in tally:
                tally[choice] += 1
    return tally
