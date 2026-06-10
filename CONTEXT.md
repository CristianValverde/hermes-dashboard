# Hermes Dashboard - Project Context

Updated: 2026-06-10

## 1) Purpose
Local analytics dashboard for Hermes sessions, token consumption, tool activity, and secondary OpenRouter cost visibility.

## 2) Stack
- Backend: Python, Flask, SQLite, requests, pandas
- Frontend: React 18 UMD + Babel standalone (runtime JSX)
- Data: `dashboard.db` with collector-driven ETL

## 3) Key entrypoints
- API/UI server: `python api/flask_app.py` or `python -m flask --app flask_app:app run --host 127.0.0.1 --port 8590` from `api/`
- Collector: `python collector.py`
- Launchers: `launch-dashboard.bat`, `launch-dashboard.ps1`, `launch-dashboard-network.ps1`, `hermes-dashboard.bat`

## 4) Important commands
- `python collector.py`
- `python collector.py --sessions-only`
- `python collector.py --credits-only`
- `python collector.py --full-refresh`
- `python scripts/openrouter-credits.py --help`
- `Invoke-WebRequest -UseBasicParsing http://localhost:8590/api/all`

## 5) Architecture summary
- `collector.py`: ingests Hermes data + OpenRouter data, migrates schema, updates aggregations and run logs.
- `api/flask_app.py`: serves `/api/all`, `/api/system`, `/api/sessions` and static SPA.
- `api/static/app.jsx`: bootstraps normalized API data and global shell UI.
- `api/static/sections.jsx`: tab-specific information models and charts.
- `api/static/styles.css`: layout, panel, chart, and responsive styling.

## 6) Data flow
- Inputs: Hermes local state/logs and OpenRouter API.
- Storage: SQLite (`dashboard.db`) tables like `sessions`, `daily_stats`, `model_stats`, `collector_runs`, `openrouter_daily_usage`, `tool_usage`.
- Output: JSON API consumed by SPA (`fetch('/api/all')`).
- Derived field: `/api/all.toolTokenUsage` attributes session token totals proportionally across tool calls in the same session. This is attribution, not direct per-call metering.

## 7) Current known issues / fragility
- Server startup can fail depending on Python env if Flask is missing; running from `api/` with Flask module is more reliable.
- Windows console encoding can crash on emoji output unless UTF-8 is set.
- Frontend build is runtime Babel/CDN (fragile vs bundled build).
- Repo often has local uncommitted changes; verify before edits.
- `api/flask_app.py` still contains pre-existing trailing whitespace outside the recent logic changes, so full-file `git diff --check` may still fail.
- Network access is supported, but it should remain opt-in through env vars or the dedicated network launcher.

## 8) Fixes applied in this session
- Resolved `/api/all` backend crash in `load_model_costs_real` by normalizing `today_sessions` into plain dicts before `.get(...)` access.
- Added `/api/all.toolTokenUsage` to expose attributed token usage by tool.
- Normalized `economicProviderUsage` and `toolTokenUsage` in `api/static/app.jsx`.
- Reworked `Tokens` information model around consumption: day, provider, model, and tool first; billing secondary.
- Replaced pastel token donuts with saturated OpenRouter-style colors and explicitly avoided low-contrast mint + ice-blue pairings.
- Removed the Management Key prompt from the dashboard UI and moved that instruction to `README.md`.
- Removed OpenRouter credits cards from the sidebar so cost no longer dominates the shell UI.
- Reworked `System` to match the newer unified dashboard treatment: stronger HUD panels, clearer operational grouping, shared chart primitives, and responsive validation in desktop + mobile.

## 9) Suggested startup checklist for future sessions
1. Confirm server is listening on `localhost:8590`.
2. Validate `GET /api/all` returns 200 before UI debugging.
3. If server fails on `flask` import, use Hermes venv Python or run Flask from the `api/` directory.
4. If Unicode print error appears, set `PYTHONIOENCODING=utf-8`.
5. Re-check git status before implementing changes.
6. When touching dashboard hierarchy, review `docs/DASHBOARD_DESIGN_DECISIONS.md` first.
7. If the user is on mobile and asks for screenshots, show them inline in the chat via image rendering/viewer; do not rely on local file links or filesystem paths.

## 10) Active decisions
- Keep Flask + SQLite architecture for now; optimize stability before major migrations.
- Treat `/api/all` as critical health endpoint: backend changes must preserve 200 response.
- Prefer Hermes venv Python for local runs to avoid missing dependency drift.
- Keep repository memory in `CONTEXT.md` as canonical startup context and refresh after meaningful structural changes.
- Cross-session dashboard UI decisions live in `docs/DASHBOARD_DESIGN_DECISIONS.md`.
- Validate each tab's information model before redesigning its presentation.
- `Tokens` is now consumption-led: primary questions are tokens by day, provider, model, and tool. OpenRouter billing stays secondary.
- Management Key instructions belong in `README.md`, not the dashboard UI.
- Default dashboard bind host is `127.0.0.1`; LAN/VPN access is opt-in via `HERMES_DASHBOARD_*` env vars or `launch-dashboard-network.ps1`.
- Do not reintroduce pastel token palettes or low-contrast mint/cyan donut combinations.
- Mobile screenshot workflow: present validation captures inline in chat; local file links and `C:\...` paths are not sufficient for mobile users.
