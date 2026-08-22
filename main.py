"""HTTP gateway for Brainstorm Stage.

The browser never sees the Mistral key: every call goes through here and out via
`mitral.llm`. Generating a panel is a sequence of a dozen-odd model calls, so the
session endpoint is slow by design — the UI shows a loading state rather than
pretending with canned dialogue. The exception is DEV_MODE (on by default), which
serves the prewritten panel in `mitral.fixture` so the UI can be built instantly.
"""
import os
import random

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from mitral.fixture import canned_deliberation, canned_extra, canned_reply, canned_session
from mitral.llm import MODEL
from mitral.personality import (
    MODES,
    Persona,
    Pitch,
    add_panellist,
    deliberate,
    first_takes,
    generate_cast,
    one_take,
    reply,
)

# Stage furniture. The model names the panellists; these just keep each one
# visually distinct on the stage.
GLYPHS = ["✦", "◆", "■", "♥", "※", "✺", "●", "▲"]
COLORS = ["#7c5ce8", "#e09a2f", "#4c9be0", "#e86a8a", "#2fb8a6", "#c05ce8", "#64748b", "#d8632f"]


class SessionRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    panellists: int = Field(default=5, ge=2, le=8)
    mode: str = Field(default="grounded")
    seed: int | None = None


class AddRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    mode: str = Field(default="grounded")
    cast: list[dict]
    pitches: list[dict] = Field(default_factory=list)


class ReplyRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    message: str = Field(min_length=1, max_length=2_000)
    persona: dict


# Vite prints the localhost URL but the browser will happily be pointed at
# 127.0.0.1 instead, and to CORS those are two different origins — allow both so
# whichever one you paste in works. FRONTEND_ORIGIN overrides, comma-separated.
DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

# Dev mode serves the prewritten panel in mitral.fixture instead of calling
# Mistral: instant, free, and the same response shape. On by default because
# that is what you want while building the UI — set DEV_MODE=0 for real output.
DEV_MODE = os.getenv("DEV_MODE", "1").lower() not in ("0", "false", "no", "")

app = FastAPI(title="Brainstorm Stage API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("FRONTEND_ORIGIN", "").split(",") if o.strip()]
    or DEFAULT_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "llm_configured": bool(os.getenv("MISTRAL_API_KEY")),
        "dev_mode": DEV_MODE,
        "model": _model(),
    }


@app.post("/api/session")
def session(body: SessionRequest) -> dict[str, object]:
    """Generate a whole panel: who's in the room, what they pitch, what wins."""
    if body.mode not in MODES:
        raise HTTPException(status_code=422, detail=f"mode must be one of {sorted(MODES)}")
    seed = body.seed if body.seed is not None else random.randrange(1 << 30)
    if DEV_MODE:
        cast, pitches = canned_session(body.panellists, body.mode, seed)
        verdict = canned_deliberation(cast)
    else:
        _require_key()
        try:
            cast = generate_cast(body.topic, body.panellists, seed, body.mode)
            pitches = first_takes(cast, body.topic, seed)
            verdict = deliberate(cast, body.topic, pitches, seed)
        except Exception as exc:
            raise _upstream(exc) from exc

    agents = [_agent(p, i) for i, p in enumerate(cast)]
    return {
        "topic": body.topic,
        "model": _model(),
        "seed": seed,
        "agents": agents,
        "pitches": [
            {"agent": agents[i]["id"], **q.model_dump()} for i, q in enumerate(pitches)
        ],
        "deliberation": {
            "plan": {"agent": _match(agents, verdict.plan_speaker), "text": verdict.plan_text},
            "test": {"agent": _match(agents, verdict.test_speaker), "text": verdict.test_text},
            "winner": {"agent": _match(agents, verdict.winner_speaker), "why": verdict.why},
        },
    }


@app.post("/api/panellist")
def panellist(body: AddRequest) -> dict[str, object]:
    """One more voice for a panel that's already on stage."""
    if body.mode not in MODES:
        raise HTTPException(status_code=422, detail=f"mode must be one of {sorted(MODES)}")
    try:
        cast = [Persona(**p) for p in body.cast]
        said = [(cast[i], Pitch(**q)) for i, q in enumerate(body.pitches) if i < len(cast)]
    except Exception as exc:
        raise HTTPException(status_code=422, detail="that isn't a valid panel") from exc
    if DEV_MODE:
        try:
            person, pitch = canned_extra(cast, body.mode)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    else:
        _require_key()
        try:
            person = add_panellist(body.topic, cast, mode=body.mode)
            pitch = one_take(person, body.topic, said)
        except ValueError as exc:  # trait pools exhausted — a real answer, not a crash
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception as exc:
            raise _upstream(exc) from exc

    agent = _agent(person, len(cast))
    return {"agent": agent, "pitch": {"agent": agent["id"], **pitch.model_dump()}}


@app.post("/api/reply")
def respond(body: ReplyRequest) -> dict[str, str]:
    """One panellist's answer to something the human said in the room."""
    try:
        persona = Persona(**body.persona)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="persona is not a valid panellist") from exc
    if DEV_MODE:
        return {"text": canned_reply(persona, body.message)}
    _require_key()
    try:
        return {"text": reply(persona, body.topic, body.message)}
    except Exception as exc:
        raise _upstream(exc) from exc


def _agent(p: Persona, i: int) -> dict[str, object]:
    """Persona plus the stage furniture that keeps them visually distinct."""
    return {
        "id": f"{_slug(p.name)}-{i}",
        "name": p.name,
        "role": p.tagline,
        "bio": p.bio,
        "glyph": GLYPHS[i % len(GLYPHS)],
        "color": COLORS[i % len(COLORS)],
        "index": i,
        "persona": p.model_dump(),
    }


def _model() -> str:
    """What the UI shows in the topic chip — and how you spot dev mode is on."""
    return "dev fixture · no API calls" if DEV_MODE else MODEL


def _require_key() -> None:
    if not os.getenv("MISTRAL_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="MISTRAL_API_KEY is not set — get one at https://console.mistral.ai and put it in .env",
        )


def _upstream(exc: Exception) -> HTTPException:
    status = getattr(exc, "status_code", None)
    if status == 429:
        return HTTPException(status_code=429, detail="Mistral rate limit hit — give it a moment and retry")
    if status == 401:
        return HTTPException(status_code=502, detail="Mistral rejected the API key")
    return HTTPException(status_code=502, detail=f"Mistral call failed: {str(exc)[:300]}")


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-") or "agent"


def _match(agents: list[dict], name: str) -> str:
    """Map a name the model returned back onto an agent id.

    The model is asked for a name off the panel list but occasionally returns it
    with a title attached, or picks nobody at all. Fall back rather than 500.
    """
    wanted = name.strip().lower()
    for agent in agents:
        if agent["name"].lower() == wanted:
            return agent["id"]
    for agent in agents:
        if agent["name"].lower() in wanted or wanted in agent["name"].lower():
            return agent["id"]
    return agents[0]["id"]
