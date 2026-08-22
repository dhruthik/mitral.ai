import asyncio

from fastapi import APIRouter, HTTPException

from mitral.engine.factory import new_session
from mitral.engine.orchestrator import Orchestrator
from mitral.llm.mock import MockLLMClient
from mitral.server.event_bus import SessionEventBus
from mitral.server.schemas import StartSessionRequest, StartSessionResponse
from mitral.server.store import SessionHandle, store

router = APIRouter()


@router.post("/sessions", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest) -> StartSessionResponse:
    session = new_session(req.idea, cast=req.cast)
    if req.max_rounds_per_room:
        session.max_rounds_per_room = req.max_rounds_per_room

    bus = SessionEventBus()
    orchestrator = Orchestrator(session, MockLLMClient(), bus)
    task = asyncio.create_task(orchestrator.run())
    store.add(SessionHandle(session=session, bus=bus, task=task))
    return StartSessionResponse(session_id=session.id)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    handle = store.get(session_id)
    if handle is None:
        raise HTTPException(status_code=404, detail="session not found")
    s = handle.session
    return {
        "session_id": s.id,
        "state": s.state.value,
        "rooms": {
            key: {
                "id": room.id,
                "title": room.title,
                "state": room.state.value,
                "round": room.round,
                "best_proposal_id": room.best_proposal_id,
            }
            for key, room in s.rooms.items()
        },
        "result": s.result.model_dump() if s.result else None,
    }


@router.get("/sessions/{session_id}/transcript")
async def get_transcript(session_id: str) -> list[dict]:
    handle = store.get(session_id)
    if handle is None:
        raise HTTPException(status_code=404, detail="session not found")
    return [event.model_dump(mode="json") for event in handle.bus.log]
