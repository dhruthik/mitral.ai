"""Thin provider-neutral wrapper around the configured chat API.

Everything else in the project goes through ``complete_json``. Select Mistral
or Claude with ``LLM_PROVIDER`` without changing the meeting code.
"""

import json
import os
import time

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "mistral").strip().lower()
if PROVIDER not in {"mistral", "claude"}:
    raise RuntimeError("LLM_PROVIDER must be 'mistral' or 'claude'")

MODEL = (
    os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
    if PROVIDER == "claude"
    else os.getenv("MISTRAL_MODEL", "mistral-large-latest")
)

# Writing a personality is a small, high-volume job — a dozen calls per session,
# each one a short character sketch. The small model does it just as well and
# several times faster, which is most of the wait on a new session.
FAST_MODEL = (
    os.getenv("CLAUDE_FAST_MODEL", "claude-haiku-4-5")
    if PROVIDER == "claude"
    else os.getenv("MISTRAL_FAST_MODEL", "mistral-small-latest")
)

_client = None


def configured() -> bool:
    key_name = "ANTHROPIC_API_KEY" if PROVIDER == "claude" else "MISTRAL_API_KEY"
    return bool(os.getenv(key_name))


def client():
    global _client
    if _client is None:
        if PROVIDER == "claude":
            from anthropic import Anthropic

            key = os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise RuntimeError("ANTHROPIC_API_KEY is not set")
            _client = Anthropic(api_key=key)
        else:
            key = os.environ.get("MISTRAL_API_KEY")
            if not key:
                raise RuntimeError("MISTRAL_API_KEY is not set — grab one from console.mistral.ai")
            _client = Mistral(api_key=key)
    return _client


def complete_json(
    system: str,
    user: str,
    *,
    seed: int | None = None,
    temperature: float = 1.0,
    retries: int = 5,
    model: str = MODEL,
) -> dict:
    """One-shot completion that is forced to return a JSON object.

    The free tier rate-limits hard (roughly a request a second), and we make
    these calls in a tight sequence, so 429s are routine rather than
    exceptional. Back off and retry instead of dying.
    """
    for attempt in range(retries):
        try:
            if PROVIDER == "claude":
                # Sonnet 5 rejects non-default sampling parameters, and Claude
                # does not support Mistral's random_seed parameter.
                resp = client().messages.create(
                    model=model,
                    max_tokens=2_048,
                    system=system + "\n\nReturn only the requested valid JSON object, with no markdown fences.",
                    messages=[{"role": "user", "content": user}],
                )
                text = "".join(block.text for block in resp.content if block.type == "text")
                return _as_object(_parse_json(text))

            resp = client().chat.complete(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
                random_seed=seed,
            )
            return _as_object(json.loads(resp.choices[0].message.content))
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status != 429 or attempt == retries - 1:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def transcribe(data: bytes, filename: str = "audio.webm") -> str:
    """Speech-to-text via Voxtral, for the "speak your topic" mic input."""
    resp = client().audio.transcriptions.complete(
        model="voxtral-mini-latest",
        file={"content": data, "file_name": filename},
    )
    return resp.text


def _parse_json(text: str) -> object:
    """Extract an object if a provider surrounds its JSON with prose/fences."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start:
            raise
        return json.loads(text[start:end + 1])


def _as_object(data: object) -> dict:
    """JSON mode guarantees valid JSON, not a top-level object.

    The model occasionally wraps a single result in an array, or in a
    one-key envelope it invented ({"panellists": [...]}), so unwrap those
    cases rather than letting callers trip over them.
    """
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return _as_object(data[0])
    if isinstance(data, dict) and len(data) == 1:
        inner = next(iter(data.values()))
        if isinstance(inner, dict) or (isinstance(inner, list) and inner):
            return _as_object(inner)
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object, got {type(data).__name__}: {data!r:.200}")
    return data
