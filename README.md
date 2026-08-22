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

### Brainstorm Stage UI

The HTML prototype has been rebuilt as a React app on one shared dark stage.
It works with demo dialogue by default and can call an OpenAI-compatible LLM
through the Python API without exposing provider keys to the browser.

```bash
npm install
npm run dev
```

In another terminal, install the Python requirements, set `LLM_API_KEY`, and run:

```bash
uvicorn main:app --reload --port 8000
```

Optional settings are documented in `.env.example`. The frontend defaults to
`http://localhost:8000` for API requests.

## Contributing

`main` is protected — no direct pushes. Work on a branch and open a PR.

```bash
git checkout -b your-name/what-youre-doing
git commit -am "what you did"
git push -u origin your-name/what-youre-doing
gh pr create
```

Get one review before merging.
