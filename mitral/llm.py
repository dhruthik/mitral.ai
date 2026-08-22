"""Thin wrapper around the Mistral chat API.

Everything else in the project goes through here, so swapping providers is a
one-file change.
"""

import json
import os

from dotenv import load_dotenv
from mistralai.client import Mistral  # note: mistralai>=2.9 moved this out of the root package

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


def complete_json(system: str, user: str, *, seed: int | None = None, temperature: float = 1.0) -> dict:
    """One-shot completion that is forced to return a JSON object."""
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
    return json.loads(resp.choices[0].message.content)
