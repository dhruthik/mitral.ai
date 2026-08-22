# Brainstorm Stage

A React recreation of the HTML prototype, redesigned as one shared dark stage with a Python gateway for optional LLM-generated ideas. The interface automatically uses demo dialogue when the API is unavailable.

## Run locally

```bash
npm install
npm run dev
```

In another terminal:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LLM_API_KEY="your-key"
uvicorn main:app --reload --port 8000
```

Open `http://localhost:5173`. API docs are at `http://localhost:8000/docs`.

## LLM configuration

The gateway calls any OpenAI-compatible `/chat/completions` endpoint. Set `LLM_API_KEY`, and optionally `LLM_BASE_URL`, `LLM_MODEL`, `FRONTEND_ORIGIN`, or frontend-side `VITE_API_URL`. The key remains in Python and is never exposed to the browser. You can swap provider logic inside `brainstorm()` without changing React.

The original prototype remains in `prototype/brainstorm-stage.html` as a reference.
