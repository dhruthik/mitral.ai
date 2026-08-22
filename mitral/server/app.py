from fastapi import FastAPI

from mitral.server.routes import router as http_router
from mitral.server.ws import router as ws_router


def create_app() -> FastAPI:
    app = FastAPI(title="mitral.ai orchestrator")
    app.include_router(http_router)
    app.include_router(ws_router)
    return app


app = create_app()
