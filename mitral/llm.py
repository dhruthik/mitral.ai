"""Thin wrapper around the Mistral chat API.

Everything else in the project goes through here, so swapping providers is a
one-file change.
"""

import json
import os
import time

from dotenv import load_dotenv
from mistralai.client import Mistral  # note: mistralai>=2.9 moved this out of the root package
from mistralai.client.errors.sdkerror import SDKError

load_dotenv()

MODEL = "mistral-large-latest"

_client: Mistral | None = None


def client() -> Mistral:
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
) -> dict:
    """One-shot completion that is forced to return a JSON object.

    The free tier rate-limits hard (roughly a request a second), and we make
    these calls in a tight sequence, so 429s are routine rather than
    exceptional. Back off and retry instead of dying.
    """
    for attempt in range(retries):
        try:
            resp = client().chat.complete(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
                random_seed=seed,
            )
            return _as_object(json.loads(resp.choices[0].message.content))
        except SDKError as e:
            if e.status_code != 429 or attempt == retries - 1:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


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
