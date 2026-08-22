"""HTTP gateway for Brainstorm Stage.

The browser never sees the Mistral key: every call goes through here and out via
`mitral.llm`. Generating a panel is a sequence of a dozen-odd model calls, so the
session endpoint is slow by design — the UI shows a loading state rather than
pretending with canned dialogue.
"""
import os
import random
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from mitral.llm import MODEL
from mitral.meeting import Meeting, llm_turn, llm_vote
from mitral.mock import MockDriver, mock_cast
from mitral.personality import (
    MODES,
    Persona,
    deliberate,
    first_takes,
    generate_cast,
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


class ReplyRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    message: str = Field(min_length=1, max_length=2_000)
    persona: dict


class MeetingRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    panellists: int = Field(default=4, ge=2, le=8)
    mode: str = Field(default="grounded")  # cast flavor: grounded | wild
    seed: int | None = None
    # auto = real Mistral panel when MISTRAL_API_KEY is set, offline mock otherwise
    engine: Literal["auto", "mock", "llm"] = "auto"
    plenary_only: bool = False


# Vite prints the localhost URL but the browser will happily be pointed at
# 127.0.0.1 instead, and to CORS those are two different origins — allow both so
# whichever one you paste in works. FRONTEND_ORIGIN overrides, comma-separated.
DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

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
        "model": MODEL,
    }


@app.post("/api/meeting")
def meeting(body: MeetingRequest) -> dict[str, object]:
    """Run one orchestrated meeting to completion and return its event log.

    The frontend plays the log back at its own pace, so this stays a plain
    request/response — no streaming needed until turns get LLM-slow.
    """
    if body.mode not in MODES:
        raise HTTPException(status_code=422, detail=f"mode must be one of {sorted(MODES)}")
    live = body.engine == "llm" or (body.engine == "auto" and bool(os.getenv("MISTRAL_API_KEY")))
    if body.engine == "llm":
        _require_key()
    seed = body.seed if body.seed is not None else random.randrange(1 << 30)
    try:
        if live:
            cast = generate_cast(body.topic, body.panellists, seed, body.mode)
            turn_fn, vote_fn = llm_turn, llm_vote
        else:
            cast = mock_cast(body.topic, body.panellists, seed, body.mode)
            driver = MockDriver(body.topic, cast, seed)
            turn_fn, vote_fn = driver.turn, driver.vote
        result = Meeting(
            body.topic,
            cast,
            turn_fn=turn_fn,
            vote_fn=vote_fn,
            seed=seed,
            working_rooms=not body.plenary_only,
            total_turn_cap=60 if live else 40,
        ).run()
    except HTTPException:
        raise
    except Exception as exc:
        raise _upstream(exc) from exc
    return {
        "topic": body.topic,
        "engine": "llm" if live else "mock",
        "model": MODEL if live else "mock",
        "seed": seed,
        "agents": _agents(cast),
        "events": [e.model_dump() for e in result.events],
        "proposals": [p.model_dump() for p in result.proposals],
        "answer": result.answer.model_dump() if result.answer else None,
        "rounds": result.rounds,
        "turns": result.turns,
    }


@app.post("/api/session")
def session(body: SessionRequest) -> dict[str, object]:
    """Generate a whole panel: who's in the room, what they pitch, what wins."""
    _require_key()
    if body.mode not in MODES:
        raise HTTPException(status_code=422, detail=f"mode must be one of {sorted(MODES)}")
    seed = body.seed if body.seed is not None else random.randrange(1 << 30)
    try:
        cast = generate_cast(body.topic, body.panellists, seed, body.mode)
        pitches = first_takes(cast, body.topic, seed)
        verdict = deliberate(cast, body.topic, pitches, seed)
    except Exception as exc:
        raise _upstream(exc) from exc

    agents = _agents(cast)
    return {
        "topic": body.topic,
        "model": MODEL,
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


@app.post("/api/reply")
def respond(body: ReplyRequest) -> dict[str, str]:
    """One panellist's answer to something the human said in the room."""
    _require_key()
    try:
        persona = Persona(**body.persona)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="persona is not a valid panellist") from exc
    try:
        return {"text": reply(persona, body.topic, body.message)}
    except Exception as exc:
        raise _upstream(exc) from exc


def _agents(cast: list[Persona]) -> list[dict]:
    return [
        {
            "id": f"{_slug(p.name)}-{i}",
            "name": p.name,
            "role": p.tagline,
            "bio": p.bio,
            "cognition": p.traits.cognition,
            "glyph": GLYPHS[i % len(GLYPHS)],
            "color": COLORS[i % len(COLORS)],
            "index": i,
            "persona": p.model_dump(),
        }
        for i, p in enumerate(cast)
    ]


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
