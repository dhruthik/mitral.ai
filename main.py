"""Provider-agnostic LLM gateway for Brainstorm Stage."""
import json
import os
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8_000)


class BrainstormRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    messages: list[Message] = Field(default_factory=list, max_length=30)


class BrainstormResponse(BaseModel):
    ideas: list[str]
    model: str


app = FastAPI(title="Brainstorm Stage API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "llm_configured": bool(os.getenv("LLM_API_KEY"))}


@app.post("/api/brainstorm", response_model=BrainstormResponse)
def brainstorm(body: BrainstormRequest) -> BrainstormResponse:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="LLM_API_KEY is not configured")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "temperature": 0.9,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Produce exactly two vivid ideas. Return only valid JSON as {\"ideas\":[\"first\",\"second\"]}. Keep each under 240 characters."},
            *[message.model_dump() for message in body.messages],
            {"role": "user", "content": f"Disney Method brainstorm topic: {body.topic}"},
        ],
    }
    request = Request(f"{base_url}/chat/completions", data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=45) as response:
            result = json.load(response)
        ideas = json.loads(result["choices"][0]["message"]["content"])["ideas"]
        if not isinstance(ideas, list) or len(ideas) != 2 or not all(isinstance(x, str) and x.strip() for x in ideas):
            raise ValueError("Invalid ideas")
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {exc.read().decode(errors='replace')[:500]}") from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=504, detail="The LLM provider could not be reached") from exc
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="The LLM provider returned an unexpected response") from exc
    return BrainstormResponse(ideas=[idea.strip() for idea in ideas], model=model)
