from mitral.models.session import Room


def next_speaker(room: Room) -> str:
    """Deterministic round-robin, with a one-shot override: if the previous
    turn directly addressed another member (`to=<agent_id>`), that member
    speaks next before round-robin resumes where it left off."""
    if room.forced_next and room.forced_next in room.member_ids:
        speaker = room.forced_next
        room.forced_next = None
        return speaker

    speaker = room.member_ids[room.next_index % len(room.member_ids)]
    room.next_index += 1
    return speaker
