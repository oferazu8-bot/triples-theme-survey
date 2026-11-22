# CLAUDE.md — Theme survey demo (triples-theme-survey)

Owner: שמשון (Shimshon). Company: טריפל אס אנרגיה מתחדשת.
GitHub: https://github.com/oferazu8-bot/triples-theme-survey (public)
Local checkout: `/workspace/survey-theme`

## Working rules
- All application code is written only through Claude Code on this box (`/home/box/.local/bin/claude`). The responsible bot defines the task, reviews, and approves; it does not write the code itself.
- Design / demo / online homepage concepts stay in Lovable. This repo is a **copy** of those concepts for an anonymous survey. Do not modify the Lovable project from this repo.
- Never deploy, merge to a deploy branch, or run `railway up` unless Ofer says «תעלה» in his own words. An agent's say-so is not approval.
- Never print, commit, or paste secrets, tokens, or keys. Refer to environment variable **names** and file **paths** only.
- Hebrew UI, RTL. Company name is «טריפל אס אנרגיה מתחדשת». Do not invent numbers.

## Commit and PR marking
Every commit must end with these trailers (a `prepare-commit-msg` hook in `.githooks/` appends them if missing):

```
Co-Authored-By: Claude <noreply@anthropic.com>
Generated-With: Claude Code
```

Enable the hook in a checkout: `git config core.hooksPath .githooks`

Every pull request must have the label `claude-code`. Do not merge unless Ofer asked.

## What this project is
Anonymous Hebrew A/B/C survey of Triple S solar homepage design concepts, so the sales team can pick a direction before a full rebuild of triplesolar.co.il.

- `/` — survey form
- `/a/` — Design A, dark homepage (current live-site direction chosen 2026-11-03)
- `/b/` — mixed: dark hero, light sections
- `/c/` — light concept-b
- `/admin/results?token=...` — admin results (token from env)
- `GET /health` — health check

This is a **demo**. It does not change the live WordPress site.

## Stack
Python 3 + Flask + Gunicorn, SQLite (or files under `DATA_DIR`). Railway Railpack builder. `requirements.txt` pins Flask 3.1.2 and Gunicorn 23.0.0. Templates/variants live in `app.py` and `static/`.

## Run and test locally
```bash
cd /workspace/survey-theme
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DATA_DIR=/tmp/theme-survey .venv/bin/gunicorn -b 127.0.0.1:8080 -w 1 --timeout 60 app:app
# health: curl -s http://127.0.0.1:8080/health
```

`.venv/` and `data/` are gitignored. Do not commit survey responses or screenshots (`shots/`).

## Deploy
- Railway project: `triples-calculators-demo` (id `8c606c0e-3b1d-4c96-8e3c-7e53ccda5a28`)
- Service: `theme-survey-demo`
- URL: https://theme-survey-demo-production.up.railway.app
- Start command: `gunicorn -b 0.0.0.0:$PORT -w 2 --timeout 60 app:app`
- Health: `/health`

See `DEPLOY.txt`. Deploy only after Ofer's «תעלה».

Source design A (unchanged Lovable): https://triplesolar-home-concept.lovable.app
Lovable project id: `d1f4b559-2a71-47e7-bba5-5a3ecb93efb2` (Triplesolar Home Concept).

## Secrets (names and paths only)
- `ADMIN_TOKEN` — Railway environment variable for `/admin/results`. Never print or commit the value. Do not rely on any default in source; set it in Railway.
- `DATA_DIR` / `DB_PATH` if used — response storage. Defaults to `./data` locally.

## Key decisions and history
- 2026-11-02: full design rebuild of the solar site; two homepage samples (Lovable vs custom) go to a short survey first.
- 2026-11-03: dark homepage (Design A) chosen as the current concept; this folder is a copy, Lovable was not modified.
- 2026-11-05: repo published as a public demo (`oferazu8-bot/triples-theme-survey`); option C (light concept-b) added later.
- Variant C assets are loaded from the WordPress staging host `triplesolar-staging-production.up.railway.app`.

## Open items
- Survey results still need Ofer / the sales team to pick a final direction for the live WordPress rebuild.
- Live site work is separate (WordPress + `/workspace/wp-staging`, `/workspace/solar-site`). Do not publish a new homepage without «תעלה».

## Conventions
- Keep the survey anonymous. Do not collect names or emails unless Ofer asks.
- Do not change live WordPress or the Lovable source project from this repo.
- `.railwayignore` excludes local venv/data/shots.
