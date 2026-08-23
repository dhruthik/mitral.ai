"""Thin wrapper around the Mistral chat API."""

import json
import os
import time

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

PROVIDER = "mistral"
MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

# Writing a personality is a small, high-volume job — a dozen calls per session,
# each one a short character sketch. The small model does it just as well and
# several times faster, which is most of the wait on a new session.
FAST_MODEL = os.getenv("MISTRAL_FAST_MODEL", "mistral-small-latest")

_client = None


def configured() -> bool:
    return bool(os.getenv("MISTRAL_API_KEY"))


def client():
    global _client
    if _client is None:
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
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        raise RuntimeError("MISTRAL_API_KEY is not set — grab one from console.mistral.ai")
    resp = Mistral(api_key=key).audio.transcriptions.complete(
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
