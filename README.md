# mitral.ai

A whimsical multi-agent brainstorming system: you give it an idea, and a cast of
AI personalities argues about it — holding meetings, forming subcommittees,
upvoting each other, and occasionally kicking someone out — until they agree on
something worth showing you.

## Docs

All planning, scoping, and division of labour lives in the design doc:

**[Design doc (Google Docs)](https://docs.google.com/document/d/1tsbtnpXFHdyMPPEJMc5Hy6sBhp6leX8fs2Kqn1FKA58/edit)**

Read it before starting anything. Right now the scope is brainstorming only; we
expand to real implementation if there's time.

## Getting started

```bash
git clone https://github.com/dhruthik/mitral.ai.git
cd mitral.ai
```

### Choose an AI provider

The panel can run on Mistral or Claude. Set the provider and matching key in
`.env`:

```env
LLM_PROVIDER=mistral
MISTRAL_API_KEY=your-key
```

or:

```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your-key
```

The default models can be overridden with `MISTRAL_MODEL`,
`MISTRAL_FAST_MODEL`, `CLAUDE_MODEL`, and `CLAUDE_FAST_MODEL`.

### Get a Mistral API key

1. Sign up at **[console.mistral.ai](https://console.mistral.ai)**.
2. Go to **API Keys** → **Create new key**, and copy it. You only get to see it
   once.
3. You may need to add a workspace/billing profile first, but the **free tier is
   enough for this project** — no card required for the experiment plan.

Then put the key in a `.env` file at the repo root:

```bash
cp .env.example .env
```

Open `.env` and paste the key after `MISTRAL_API_KEY=`. `.env` is gitignored —
never commit your key. Everything else in `.env.example` is optional and already
defaults to the right thing for local dev.

### Running it

Backend (serves the API and is the only thing that ever sees your key):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend, in a second terminal:

```bash
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`).

Check the key is wired up correctly:

```bash
curl http://localhost:8000/api/health
```

`{"status":"ok","llm_configured":true,...}` means you're good. If
`llm_configured` is `false`, the backend didn't find `MISTRAL_API_KEY` — check
`.env` is in the repo root and restart uvicorn.

### Dev mode

`DEV_MODE=1` means nothing calls Mistral: every endpoint serves the prewritten
panel in `mitral/fixture.py`. Sessions are instant and free, which is what you
want while working on the UI — but it is always the same eight panellists, always
talking about a night cafe, whatever topic you type. The topic chip reads
`dev fixture · no API calls` when it's on.

It is off by default: set `DEV_MODE=1` in `.env` and restart uvicorn to use it.

### What actually runs

There is no canned dialogue: the panellists, their opening pitches, the plan and
stress-test beats, the verdict, and every reply to you are all generated per
session. `POST /api/session` is therefore a dozen sequential Mistral calls and
takes roughly a minute — the UI shows a casting screen while it works. Fewer
panellists is faster.

You can also drive the same engine from the CLI without the web app:

```bash
python -m mitral.personality "a coffee shop that's only open at night" -n 5 --pitch
```

Add `--mode wild` for eccentric outsiders instead of grounded colleagues, or
`--traits-only` to see the sampled traits with no API calls at all.

## Contributing

`main` is protected — no direct pushes. Work on a branch and open a PR.

```bash
git checkout -b your-name/what-youre-doing
git commit -am "what you did"
git push -u origin your-name/what-youre-doing
gh pr create
```

Merge it once it's green — no review required.
