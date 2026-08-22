from mitral.engine.turn_taking import next_speaker


def test_round_robin_wraps(session):
    room = session.rooms["room0"]  # members: d, a, w
    order = [next_speaker(room) for _ in range(5)]
    assert order == ["d", "a", "w", "d", "a"]


def test_forced_next_overrides_round_robin_once(session):
    room = session.rooms["room0"]
    assert next_speaker(room) == "d"
    room.forced_next = "w"
    assert next_speaker(room) == "w"
    # resumes round-robin from where it left off (index 1 -> "a")
    assert next_speaker(room) == "a"
