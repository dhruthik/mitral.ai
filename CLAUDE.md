# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

mitral.ai / "Brainstorm Stage": you give it a topic, and a cast of LLM-written
personalities pitch ideas, stress-test the strongest one, and pick a winner.
A React (Vite) frontend talks to a FastAPI gateway, which is the only thing that
ever sees the Mistral API key.

## Commands

Backend:

```bash
source .venv/bin/activate && uvicorn main:app --reload --port 8000
```

Frontend (second terminal): `npm run dev` (Vite, port 5173) · `npm run build` · `npm run preview`

**Dev mode is on by default** (`DEV_MODE=1`): every endpoint serves the prewritten
panel in `mitral/fixture.py` instead of calling Mistral — instant, free, same response
shape, and the topic chip in the UI reads `dev fixture · no API calls` so you can see
it. Always the same eight panellists talking about a night cafe regardless of the topic
you type. Set `DEV_MODE=0` in `.env` (and restart uvicorn) for real generation.

Check the key is wired: `curl http://localhost:8000/api/health` — `llm_configured: false`
means `MISTRAL_API_KEY` isn't in the root `.env`.

Drive the engine without the web app (fastest way to iterate on prompts):

```bash
python -m mitral.personality "a coffee shop that's only open at night" -n 5 --pitch
```

`--traits-only` prints the sampled traits with **no API calls** — use it whenever the
change is to the sampler rather than the prompts. `--seed N` makes a cast reproducible,
`--mode wild|grounded`, `--json` for raw output.

There is no test suite and no linter configured. There is no `vite.config.js` — Vite
runs on defaults with `@vitejs/plugin-react` auto-detected.

## Architecture

Three layers, each one file deep:

- `mitral/llm.py` — the *only* place that touches the Mistral SDK. `complete_json()`
  forces JSON mode, retries 429s with exponential backoff (the free tier rate-limits at
  roughly a request a second and we call in tight sequence), and unwraps the
  single-key envelopes / stray arrays the model sometimes returns. Swapping providers
  is meant to be a one-file change. Two models: `MODEL` (large, for deliberation),
  `FAST_MODEL` (small, for persona writing — a dozen short calls per session).
- `mitral/personality.py` — all the generation logic and prompts, plus a CLI. No HTTP.
- `main.py` — FastAPI. Validation, CORS, error mapping, and the "stage furniture"
  (glyph/colour/id per agent) that the model doesn't produce.
- `src/` — React. `api.js` is the only module that fetches; `App.jsx` holds all state
  and replays the returned session as timed beats.

### The anti-convergence design (read before touching personality.py)

The whole point is panellists who don't collapse into the same three ideas. Three
mechanisms enforce that, and they're easy to break accidentally:

1. **Traits are dealt without replacement** on orthogonal axes — `COGNITION` (how they
   generate ideas), a lens, and a voice. No two agents can share one. Pool size caps
   panel size; exhausting a pool raises `ValueError`, surfaced as HTTP 409.
2. **Voice/temperament is independent of cognition on purpose.** The funny one is funny
   in delivery and still reasons rigorously. Prompts say this explicitly; don't let a
   "voice" become a proxy for intelligence.
3. **Generation is sequential, not parallel.** Each persona sees the bios already
   written and is told not to reuse a career; each pitch sees prior *mechanisms* and
   must move a different lever. `_collides()` catches the model plagiarising an earlier
   bio verbatim and re-rolls (up to 3 attempts, dropping the seed).

Two modes share the same machinery, differing only in which pools they deal from and
which system prompt they use: `grounded` (STAKE + TEMPERAMENT — ordinary colleagues,
the default, for real work) and `wild` (LENS + VOICE — eccentric outsiders). `MODES`
maps mode → (lens_pool, voice_pool).

Exactly one panellist per run gets high `dominance`, otherwise the forceful archetype
monologues.

### Session flow

`POST /api/session` is ~a dozen *sequential* Mistral calls and takes roughly a minute:
`generate_cast` → `first_takes` (one pitch per panellist, each aware of prior pitches)
→ `deliberate` (one call producing the plan beat, the stress-test beat, and the
winner). That slowness is by design — there is no canned dialogue anywhere. The UI
shows a casting screen; fewer panellists is faster.

The frontend receives the *entire* session up front and animates it locally, so
Pause/Resume and the idea board are pure client state. Only `/api/panellist` (add a
voice mid-session, sending the existing cast so the newcomer stays orthogonal) and
`/api/reply` (one panellist answers the human) hit the network afterwards. `App.jsx`
keeps the authoritative session in a `useRef` and mutates it when a panellist is added
so quorum and @mentions stay in step.

The model returns speaker *names*, not ids; `_match()` in `main.py` maps them back and
falls back to the first agent rather than 500ing.

## Conventions

- Comments explain *why*, especially where the code is defending against a specific
  model failure (`_as_object`, `_collides`, `_match`, the CORS origin list). Keep that
  tone; don't strip them as noise.
- Prompts live as module-level `SYSTEM` constants next to the function that sends them.
  Their "Hard rules" sections are load-bearing — edit deliberately.
- Persona/Pitch/Deliberation are Pydantic models; the API passes `persona.model_dump()`
  round-trips through the browser, so changing those shapes breaks in-flight sessions.
- `docs/conversation-flow.md` describes a room-based multi-agent orchestrator that is
  **designed but not implemented**. Don't read it as a description of current code.
  `docs/traits.md`, `sample-panels.md`, `example-run.md` document the current system.
- `prototype/brainstorm-stage.html` is the original single-file mockup, superseded by
  `src/`.

## Repo

`main` is protected. Branch, PR, one review before merging. Never commit `.env`.
