import asyncio

from fastapi.testclient import TestClient

from mitral.server.app import create_app


def test_full_session_over_http_with_no_api_key():
    app = create_app()
    with TestClient(app) as client:
        resp = client.post(
            "/sessions", json={"idea": "a coffee shop that's only open at night", "max_rounds_per_room": 3}
        )
        assert resp.status_code == 200
        session_id = resp.json()["session_id"]

        async def wait_for_conclusion():
            for _ in range(200):
                snap = client.get(f"/sessions/{session_id}").json()
                if snap["state"] == "concluded":
                    return snap
                await asyncio.sleep(0.01)
            raise AssertionError("session never concluded")

        snapshot = asyncio.run(wait_for_conclusion())
        assert snapshot["result"] is not None
        assert snapshot["result"]["winner_room_id"] in ("room0", "room1")

        transcript = client.get(f"/sessions/{session_id}/transcript").json()
        assert transcript[0]["type"] == "session_started"
        assert transcript[-1]["type"] == "session_ended"


def test_unknown_session_returns_404():
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/sessions/does-not-exist").status_code == 404
        assert client.get("/sessions/does-not-exist/transcript").status_code == 404
