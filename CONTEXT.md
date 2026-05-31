# Hermes Dashboard - Project Context

Updated: 2026-05-31

## 1) Purpose
Local analytics dashboard for Hermes sessions and OpenRouter usage/costs.

## 2) Stack
- Backend: Python, Flask, SQLite, requests, pandas
- Frontend: React 18 UMD + Babel standalone (runtime JSX)
- Data: `dashboard.db` with collector-driven ETL

## 3) Key entrypoints
- API/UI server: `python api/flask_app.py` (http://localhost:8590)
- Collector: `python collector.py`
- Launchers: `launch-dashboard.bat`, `launch-dashboard.ps1`, `hermes-dashboard.bat`

## 4) Important commands
- `python collector.py`
- `python collector.py --sessions-only`
- `python collector.py --credits-only`
- `python collector.py --full-refresh`
- `python scripts/openrouter-credits.py --help`

## 5) Architecture summary
- `collector.py`: ingests Hermes data + OpenRouter data, migrates schema, updates aggregations and run logs.
- `api/flask_app.py`: serves `/api/all`, `/api/system`, `/api/sessions` and static SPA.
- `api/static/*`: React dashboard sections, components, i18n, styles.

## 6) Data flow
- Inputs: Hermes local state/logs and OpenRouter API.
- Storage: SQLite (`dashboard.db`) tables like `sessions`, `daily_stats`, `model_stats`, `collector_runs`, `openrouter_daily_usage`.
- Output: JSON API consumed by SPA (`fetch('/api/all')`).

## 7) Current known issues / fragility
- Server startup can fail depending on Python env if Flask is missing.
- Windows console encoding can crash on emoji output unless UTF-8 is set.
- Frontend build is runtime Babel/CDN (fragile vs bundled build).
- Repo often has local uncommitted changes; verify before edits.

## 8) Fixes applied in this session
- Resolved `/api/all` backend crash in `load_model_costs_real` by normalizing `today_sessions` into plain dicts before `.get(...)` access.
- Verified `/api/all` returns HTTP 200.

## 9) Suggested startup checklist for future sessions
1. Confirm server is listening on `localhost:8590`.
2. Validate `GET /api/all` returns 200 before UI debugging.
3. If server fails on `flask` import, use Hermes venv Python.
4. If Unicode print error appears, set `PYTHONIOENCODING=utf-8`.
5. Re-check git status before implementing changes.

## 10) Active decisions
- Keep Flask + SQLite architecture for now; optimize stability before major migrations.
- Treat `/api/all` as critical health endpoint: backend changes must preserve 200 response.
- Prefer Hermes venv Python for local runs to avoid missing dependency drift.
- Keep repository memory in `CONTEXT.md` as canonical startup context and refresh after meaningful structural changes.
