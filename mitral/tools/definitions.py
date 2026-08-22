"""Tool schemas each agent can invoke on its turn, shaped so a real LLM's
tool-use API (Anthropic-style) can be handed TOOL_SCHEMAS directly later."""

from typing import Any

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "speak": {
        "description": (
            "Say something to the room, optionally directly to one member "
            "(or to \"you\", the user), optionally pinning it as an idea."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "kind": {"type": "string", "enum": ["idea", "challenge", "build", "reaction", "summary"]},
                "to": {"type": ["string", "null"]},
                "as_idea": {"type": "boolean"},
            },
            "required": ["content", "kind"],
        },
    },
    "upvote_idea": {
        "description": "Upvote another agent's pinned idea in this room.",
        "parameters": {
            "type": "object",
            "properties": {"proposal_id": {"type": "string"}},
            "required": ["proposal_id"],
        },
    },
    "knock_out": {
        "description": (
            "Comedically knock out another active member of your room; "
            "they bounce back on their own before their next turn."
        ),
        "parameters": {
            "type": "object",
            "properties": {"target_id": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["target_id"],
        },
    },
    "propose_wrap": {
        "description": "Vote to end this room's breakout early so it can head to the Quorum.",
        "parameters": {"type": "object", "properties": {}},
    },
    "cast_vote": {
        "description": "Quorum phase only: vote for the room whose idea should win.",
        "parameters": {
            "type": "object",
            "properties": {"room_choice": {"type": "string", "enum": ["room0", "room1"]}},
            "required": ["room_choice"],
        },
    },
}
