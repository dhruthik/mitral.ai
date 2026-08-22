"""Stance-templated dialogue, ported from the UI team's mocked prototype
(prototype/brainstorm-stage.html on origin/brainstorm-stage-prototype) so the
Mock LLM's default output matches what that frontend already demos."""

import random
import re

STOPWORDS = {
    "a", "an", "the", "that", "this", "for", "with", "and", "or", "of", "to",
    "in", "on", "at", "is", "are", "only", "open", "its", "it's", "my", "our",
    "your",
}


def keywords(topic: str) -> list[str]:
    words = re.sub(r"[^a-z0-9\s'-]", "", topic.lower()).split()
    kw = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    return kw or ["this"]


SEED = {
    "adj": ["tiny", "members-only", "glow-in-the-dark", "pay-what-you-want", "invite-only", "neighborhood", "secret", "weekly", "hand-made"],
    "format": ["pop-up", "passport", "club", "ritual", "wall of notes", "scavenger hunt", "zine", "membership card", "swap meet"],
    "verb": ["celebrates", "gamifies", "crowdsources", "reinvents", "flips the script on", "builds a cult following around"],
    "aud": ["regulars", "night owls", "first-timers", "strangers", "locals", "the curious"],
}


def gen_seed(kws: list[str], rng: random.Random) -> str:
    return (
        f"a {rng.choice(SEED['adj'])} {rng.choice(SEED['format'])} that "
        f"{rng.choice(SEED['verb'])} {rng.choice(kws)} for {rng.choice(SEED['aud'])}"
    )


def fill(tpl: str, slots: dict[str, str]) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: str(slots.get(m.group(1), "")), tpl)


TEMPLATES: dict[str, dict[str, list[str]]] = {
    "opener": {
        "dreamer": [
            "Ooh — {topic}?! Welcome to {room}. No judging, only dreaming. GO.",
            "Okay {room}, rule one: for the next ten minutes every idea about {topic} is a great idea.",
        ],
        "skeptic": [
            "{room}. Where ideas about {topic} come to get stress-tested. Who wants to go first?",
            "Hmm. {topic}. Fine — {room} is open, bring me something I can't poke a hole in.",
        ],
        "pragmatist": [
            "Welcome to {room}. Scope: {topic}. Budget: tiny. Impress me anyway.",
            "Okay {room}, concretely: {topic}. What ships in two weeks?",
        ],
        "advocate": [
            "{room} is open! First — picture the actual person who needs {topic}. Hold them in mind.",
            "Before we brainstorm {topic}, {room}: think of one real person it would delight.",
        ],
        "wildcard": [
            "I hereby declare {room} a normal-free zone. {topic}, but make it weird.",
            "{room}! {topic}! My antenna is ALREADY tingling.",
        ],
    },
    "idea": {
        "dreamer": [
            "What if we tried {seed}?! I can SEE it — tell me you can't see it!",
            "Hear me out: {seed}. Goosebumps, right?!",
        ],
        "skeptic": [
            "Fine, here's one I'd actually defend: {seed}. Unsexy, but it works.",
            "Against my better judgment: {seed}. At least it's falsifiable.",
        ],
        "pragmatist": [
            "Okay, concretely: {seed}. Cheap to test, easy to kill if it flops.",
            "Small bet: {seed}. If twenty people show up twice, we double down.",
        ],
        "advocate": [
            "Picture a first-timer discovering {seed}. They'd tell a friend by morning.",
            "For the person who almost didn't come: {seed}. That's who it's for.",
        ],
        "wildcard": [
            "Total left turn: {seed}. The weirdness IS the marketing.",
            "Splicing two bad ideas into a great one: {seed}. You're welcome.",
        ],
    },
    "challenge": {
        "skeptic": [
            "Hmm. {prevName}, walk me through it — who shows up for that TWICE? Numbers, please.",
            "{prevName}, that's adorable. Now defend it against a rainy Tuesday in February.",
        ],
        "pragmatist": [
            "{prevName}, love the energy — but what does v1 cost? Scope it or drop it.",
            "Before anyone claps: {prevName}, who runs this on day 30 when the novelty's gone?",
        ],
    },
    "build": {
        "dreamer": ["YES and — stack {prevName}'s thing with {seed}! One idea wearing two hats!"],
        "advocate": ["Building on {prevName}: make it personal. Remember their name, their order, their thing. That's the retention."],
        "wildcard": ["Take {prevName}'s idea, splice in {seed}. Chaos, but organized chaos."],
        "pragmatist": ["{prevName}'s idea, minus the expensive half, plus a waiting list. Now it ships."],
        "skeptic": ["{prevName}'s idea survives if — and only if — we cut everything that needs a permit."],
    },
    "reaction": {
        "dreamer": ["I'm obsessed. Somebody write that down before it escapes!"],
        "skeptic": ["Well. That's... not the worst thing I've heard today. High praise."],
        "pragmatist": ["Logged. Moving on before we get carried away."],
        "advocate": ["That would genuinely make someone's whole day. Keep it."],
        "wildcard": ["My antenna is tingling. That's either a great sign or the wifi."],
    },
    "pitch": {
        "dreamer": ["{room} brought the magic. Our best: {best}. You're welcome, everyone."],
        "skeptic": ["{room} report. One idea survived me: {best}. That should tell you something."],
        "pragmatist": ["{room} report: {best}. Under budget. Naturally."],
        "advocate": ["{room}'s pick: {best}. Because someone out there needs exactly that."],
        "wildcard": ["{room} sends its champion: {best}. It chose itself, honestly."],
    },
    "closer": [
        "Quorum verdict on {topic}: “{winner}” takes it, {votes}. The runner-up folds into phase two. Two rooms, one plan — good session, everyone.",
    ],
}
