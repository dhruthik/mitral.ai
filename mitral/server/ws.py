from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from mitral.server.store import store

router = APIRouter()


@router.websocket("/sessions/{session_id}/stream")
async def stream_session(websocket: WebSocket, session_id: str) -> None:
    handle = store.get(session_id)
    if handle is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    for event in handle.bus.log:
        await websocket.send_json(event.model_dump(mode="json"))

    queue = handle.bus.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event.model_dump(mode="json"))
            if event.type == "session_ended":
                break
    except WebSocketDisconnect:
        pass
    finally:
        handle.bus.unsubscribe(queue)
